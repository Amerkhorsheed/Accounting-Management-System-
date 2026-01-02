import os
import json
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime

from django.conf import settings
from django.core.management import call_command
from django.http import FileResponse

from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response


class BackupViewSet(viewsets.ViewSet):
    lookup_value_regex = r'[^/]+'
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'create', 'download', 'restore', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def _backups_dir(self) -> Path:
        backups_dir = Path(settings.BASE_DIR) / 'backups'
        backups_dir.mkdir(parents=True, exist_ok=True)
        return backups_dir

    def _safe_backup_path(self, filename: str) -> Path:
        backups_dir = self._backups_dir().resolve()
        candidate = (backups_dir / filename).resolve()
        if backups_dir not in candidate.parents and candidate != backups_dir:
            raise ValueError('Invalid backup filename')
        if candidate.suffix.lower() not in {'.zip', '.amsbackup'}:
            raise ValueError('Invalid backup extension')
        return candidate

    def list(self, request):
        backups_dir = self._backups_dir()
        items = []
        for p in backups_dir.glob('*.zip'):
            st = p.stat()
            items.append({
                'filename': p.name,
                'size': st.st_size,
                'created_at': datetime.fromtimestamp(st.st_mtime).isoformat(),
            })
        for p in backups_dir.glob('*.amsbackup'):
            st = p.stat()
            items.append({
                'filename': p.name,
                'size': st.st_size,
                'created_at': datetime.fromtimestamp(st.st_mtime).isoformat(),
            })
        items.sort(key=lambda x: x['created_at'], reverse=True)
        return Response({'results': items})

    def create(self, request):
        include_media = bool(request.data.get('include_media', False))
        created_by = getattr(request.user, 'username', None)

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ams_backup_{ts}.amsbackup"
        backup_path = self._backups_dir() / filename

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                db_json_path = tmp_dir_path / 'db.json'
                meta_path = tmp_dir_path / 'metadata.json'

                with open(db_json_path, 'w', encoding='utf-8') as f:
                    call_command(
                        'dumpdata',
                        '--natural-foreign',
                        '--natural-primary',
                        '--indent',
                        '2',
                        '--exclude',
                        'admin.logentry',
                        '--exclude',
                        'sessions.session',
                        stdout=f,
                    )

                metadata = {
                    'format': 'amsbackup',
                    'created_at': datetime.now().isoformat(),
                    'created_by': created_by,
                    'database': {
                        'engine': settings.DATABASES.get('default', {}).get('ENGINE'),
                        'name': settings.DATABASES.get('default', {}).get('NAME'),
                        'host': settings.DATABASES.get('default', {}).get('HOST'),
                    },
                    'include_media': include_media,
                }

                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)

                with zipfile.ZipFile(backup_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                    zf.write(meta_path, arcname='metadata.json')
                    zf.write(db_json_path, arcname='db.json')

                    if include_media:
                        media_root = Path(getattr(settings, 'MEDIA_ROOT', ''))
                        if media_root and media_root.exists():
                            for root, _, files in os.walk(media_root):
                                for file in files:
                                    fp = Path(root) / file
                                    rel = fp.relative_to(media_root)
                                    zf.write(fp, arcname=str(Path('media') / rel))

            st = backup_path.stat()
            return Response(
                {
                    'filename': filename,
                    'size': st.st_size,
                    'created_at': datetime.fromtimestamp(st.st_mtime).isoformat(),
                    'download_url': f"/api/v1/core/backups/{filename}/download/",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            if backup_path.exists():
                try:
                    backup_path.unlink()
                except Exception:
                    pass
            return Response(
                {'detail': 'فشل إنشاء النسخة الاحتياطية', 'code': 'BACKUP_CREATE_FAILED', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        try:
            backup_path = self._safe_backup_path(pk)
        except ValueError:
            return Response({'detail': 'اسم ملف غير صالح', 'code': 'INVALID_FILENAME'}, status=400)

        if not backup_path.exists():
            return Response({'detail': 'النسخة الاحتياطية غير موجودة', 'code': 'NOT_FOUND'}, status=404)

        return FileResponse(
            open(backup_path, 'rb'),
            as_attachment=True,
            filename=backup_path.name,
            content_type='application/octet-stream',
        )

    @action(detail=False, methods=['post'], url_path='restore')
    def restore(self, request):
        confirm = (request.data.get('confirm') or '').strip().upper()
        if confirm != 'RESTORE':
            return Response(
                {'detail': 'يجب تأكيد الاستعادة بإرسال قيمة confirm=RESTORE', 'code': 'CONFIRM_REQUIRED'},
                status=400,
            )

        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'detail': 'ملف النسخة الاحتياطية مطلوب', 'code': 'FILE_REQUIRED'}, status=400)

        restore_media = str(request.data.get('restore_media', 'true')).lower() == 'true'
        replace_media = str(request.data.get('replace_media', 'false')).lower() == 'true'

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)
                uploaded_path = tmp_dir_path / Path(uploaded.name).name
                with open(uploaded_path, 'wb') as f:
                    for chunk in uploaded.chunks():
                        f.write(chunk)

                with zipfile.ZipFile(uploaded_path, 'r') as zf:
                    names = set(zf.namelist())
                    if 'db.json' not in names or 'metadata.json' not in names:
                        return Response(
                            {'detail': 'ملف النسخة الاحتياطية غير صالح', 'code': 'INVALID_BACKUP'},
                            status=400,
                        )

                    for member in zf.infolist():
                        member_name = member.filename
                        if member_name.endswith('/'):
                            continue
                        dest = (tmp_dir_path / member_name).resolve()
                        if tmp_dir_path.resolve() not in dest.parents and dest != tmp_dir_path.resolve():
                            return Response(
                                {'detail': 'ملف النسخة الاحتياطية غير صالح', 'code': 'INVALID_BACKUP'},
                                status=400,
                            )
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member, 'r') as src, open(dest, 'wb') as out:
                            out.write(src.read())

                meta_path = tmp_dir_path / 'metadata.json'
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    if (meta or {}).get('format') != 'amsbackup':
                        return Response(
                            {'detail': 'ملف النسخة الاحتياطية غير صالح', 'code': 'INVALID_BACKUP'},
                            status=400,
                        )
                except Exception:
                    return Response(
                        {'detail': 'ملف النسخة الاحتياطية غير صالح', 'code': 'INVALID_BACKUP'},
                        status=400,
                    )

                db_json_path = tmp_dir_path / 'db.json'

                call_command('flush', '--noinput')
                call_command('loaddata', str(db_json_path))
                call_command('migrate', '--noinput')

                if restore_media:
                    media_root = Path(getattr(settings, 'MEDIA_ROOT', ''))
                    extracted_media = tmp_dir_path / 'media'
                    if media_root and extracted_media.exists():
                        media_root.mkdir(parents=True, exist_ok=True)

                        if replace_media:
                            for root, dirs, files in os.walk(media_root):
                                for file in files:
                                    try:
                                        (Path(root) / file).unlink()
                                    except Exception:
                                        pass
                                for d in dirs:
                                    try:
                                        (Path(root) / d).rmdir()
                                    except Exception:
                                        pass

                        for root, _, files in os.walk(extracted_media):
                            for file in files:
                                src = Path(root) / file
                                rel = src.relative_to(extracted_media)
                                dst = media_root / rel
                                dst.parent.mkdir(parents=True, exist_ok=True)
                                dst.write_bytes(src.read_bytes())

            return Response({'status': 'restored'})

        except Exception as e:
            return Response(
                {'detail': 'فشل استعادة النسخة الاحتياطية', 'code': 'RESTORE_FAILED', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, pk=None):
        try:
            backup_path = self._safe_backup_path(pk)
        except ValueError:
            return Response({'detail': 'اسم ملف غير صالح', 'code': 'INVALID_FILENAME'}, status=400)

        if not backup_path.exists():
            return Response({'detail': 'النسخة الاحتياطية غير موجودة', 'code': 'NOT_FOUND'}, status=404)

        try:
            backup_path.unlink()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'detail': 'فشل حذف النسخة الاحتياطية', 'code': 'DELETE_FAILED', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
