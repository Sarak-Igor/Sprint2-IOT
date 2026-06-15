import boto3
from .config import settings

class R2StorageClient:
    """
    Cliente Singleton para interação com o Cloudflare R2 via API S3.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(R2StorageClient, cls).__new__(cls)
            cls._instance._client = boto3.client(
                service_name='s3',
                endpoint_url=settings.r2_endpoint_url,
                aws_access_key_id=settings.r2_access_key_id,
                aws_secret_access_key=settings.r2_secret_access_key,
                region_name='auto'
            )
        return cls._instance

    def upload_file(self, file_content: bytes, file_name: str, content_type: str = "application/pdf") -> bool:
        """
        Realiza o upload de um arquivo para o bucket R2.
        """
        try:
            self._client.put_object(
                Bucket=settings.r2_bucket_name,
                Key=file_name,
                Body=file_content,
                ContentType=content_type
            )
            return True
        except Exception as e:
            print(f"[ERRO] Falha no upload para R2: {e}")
            return False

    def get_download_url(self, file_name: str, expires_in: int = 3600) -> str:
        """
        Gera uma URL pré-assinada para download temporário.
        """
        try:
            url = self._client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.r2_bucket_name, 'Key': file_name},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            print(f"[ERRO] Falha ao gerar URL R2: {e}")
            return ""

# Instância global
storage_client = R2StorageClient()
