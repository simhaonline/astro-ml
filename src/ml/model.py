import torch, torch.onnx, joblib, boto3, os, json, io
from datetime import datetime
import pytorch_lightning as pl
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, roc_auc_score

S3_BUCKET = os.getenv("S3_BUCKET", "astro-ml-models")

class AstroLSTM(pl.LightningModule):
    def __init__(self, n_features: int, lr: float = 3e-4):
        super().__init__()
        self.save_hyperparameters()
        self.lstm = torch.nn.LSTM(n_features, 128, 3, batch_first=True, dropout=0.2)
        self.fc = torch.nn.Sequential(torch.nn.Dropout(0.5), torch.nn.Linear(128, 64), torch.nn.ReLU(), torch.nn.Linear(64, 1))
        self.criterion = torch.nn.BCEWithLogitsLoss()

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :]).squeeze()

    def training_step(self, batch, _):
        x, y = batch
        loss = self.criterion(self(x), y.float())
        self.log("train_loss", loss)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)

    def predict(self, X: pd.DataFrame) -> Dict:
        self.eval()
        with torch.no_grad():
            X = torch.tensor(X.values).unsqueeze(1)
            logits = self(X)
            prob = torch.sigmoid(logits).item()
            signal = "LONG" if prob > 0.5 else "SHORT"
            kelly = max(0, min(0.25, (prob * 2 - 1)))
            return {"signal": signal, "confidence": prob, "kelly_fraction": kelly}

    def push_to_registry(self, ticker: str, horizon: int):
        version = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        pt_key = f"{ticker}/h{horizon}/{version}.pt"
        buffer = io.BytesIO()
        torch.save(self.state_dict(), buffer)
        buffer.seek(0)
        boto3.client("s3").upload_fileobj(buffer, S3_BUCKET, pt_key)
        # ONNX
        onnx_key = f"{ticker}/h{horizon}/{version}.onnx"
        dummy = torch.randn(1, 1, self.hparams.n_features)
        onnx_path = f"/tmp/{version}.onnx"
        torch.onnx.export(self, dummy, onnx_path, input_names=["input"], output_names=["direction"], dynamic_axes={"input": {0: "batch"}})
        boto3.client("s3").upload_file(onnx_path, S3_BUCKET, onnx_key)
        # latest pointer
        boto3.client("s3").put_object(Bucket=S3_BUCKET, Key=f"{ticker}/h{horizon}/latest.json", Body=json.dumps({"version": version}))

    @classmethod
    def load_from_registry(cls, ticker: str, horizon: int):
        obj = boto3.client("s3").get_object(Bucket=S3_BUCKET, Key=f"{ticker}/h{horizon}/latest.json")
        version = json.loads(obj["Body"].read())["version"]
        pt_key = f"{ticker}/h{horizon}/{version}.pt"
        buffer = io.BytesIO()
        boto3.client("s3").download_fileobj(S3_BUCKET, pt_key, buffer)
        buffer.seek(0)
        # dummy n_features inferred from first row
        dummy_df = pd.read_parquet(f"s3://{S3_BUCKET}/features/{ticker}.parquet", columns=[])
        n_features = len(dummy_df.columns) - 1
        model = cls(n_features=n_features)
        model.load_state_dict(torch.load(buffer, map_location="cpu"))
        return model
