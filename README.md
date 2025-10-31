# astro-ml
High-Precision Sidereal Ephemeris + 400+ Astro-Features + ML Predictions

# 1. Clone (empty dir)
git clone https://github.com/you/astro-ml.git && cd astro-ml

# 2. Infra (EKS + S3)
make infra   # terraform apply (takes ~12 min)

# 3. Build, push, deploy
make deploy  # docker build → helm upgrade (~3 min)

# 4. Port-forward to laptop
make port-forward
open http://localhost:8888/docs

# 5. Verify
curl http://localhost:8888/api/now
curl http://localhost:8888/api/predict \
  -X POST -H "Content-Type: application/json" \
  -d '{"ticker":"Gold","horizon":1}'
