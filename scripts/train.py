#!/usr/bin/env python3
import os, argparse, pandas as pd
from datetime import datetime, timedelta
from src.ml.model import AstroLSTM
from src.astro.features import make_features
from src.data.ohlcv import load_ohlcv

S3_BUCKET = os.getenv("S3_BUCKET", "astro-ml-models")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--horizon", type=int, default=1)
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--lr", type=float, default=3e-4)
    args = parser.parse_args()

    # 5-year look-back
    end = datetime.utcnow()
    start = end - timedelta(days=365*5)
    price = load_ohlcv(args.ticker, start, end)
    astro = make_features(args.ticker, pd.date_range(start, end, freq="D"))
    df = pd.concat([price, astro], axis=1).dropna()
    df["target"] = (df["close"].pct_change(args.horizon).shift(-args.horizon) > 0).astype(int)
    df = df.dropna()

    feature_cols = [c for c in df.columns if c not in {"open", "high", "low", "close", "volume", "target"}]
    X = df[feature_cols].astype("float32")
    y = df["target"].astype("float32")

    import torch, pytorch_lightning as pl
    from torch.utils.data import TensorDataset, DataLoader
    ds = TensorDataset(torch.tensor(X.values).unsqueeze(1), torch.tensor(y.values))
    loader = DataLoader(ds, batch_size=1024, shuffle=True)

    model = AstroLSTM(n_features=len(feature_cols), lr=args.lr)
    trainer = pl.Trainer(max_epochs=args.epochs, gpus=1 if torch.cuda.is_available() else 0, logger=False)
    trainer.fit(model, loader)
    model.push_to_registry(args.ticker, args.horizon)
    print("✅ model pushed to s3", args.ticker, args.horizon)

if __name__ == "__main__":
    main()
