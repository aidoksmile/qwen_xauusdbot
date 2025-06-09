from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class GoogleDriveUploader:
    def __init__(self, credentials_file):
        self.creds = Credentials.from_authorized_user_file(credentials_file)
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def upload_file(self, file_path, folder_id=None):
        """Загрузка файла в Google Drive"""
        try:
            file_metadata = {'name': os.path.basename(file_path)}
            if folder_id:
                file_metadata['parents'] = [folder_id]
                
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            ).execute()
            
            return file.get('webViewLink')
            
        except Exception as e:
            logger.error(f"Google Drive upload error: {e}")
            return None

class Backtester:
    def __init__(self, signals=None, returns=None):
        self.signals = signals
        self.returns = returns
        self.drive_uploader = None
    
    def set_drive_uploader(self, credentials_file):
        """Настройка загрузки в Google Drive"""
        self.drive_uploader = GoogleDriveUploader(credentials_file)
    
    def plot_equity_curve(self, filename='images/equity_curve.png'):
        """Генерация и сохранение графика equity"""
        plt.figure(figsize=(12, 6))
        self.returns.cumsum().plot()
        plt.title('Equity Curve')
        plt.savefig(filename)
        plt.close()
        
        if self.drive_uploader:
            drive_link = self.drive_uploader.upload_file(filename)
            return drive_link
        return filename
