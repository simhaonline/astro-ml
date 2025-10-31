output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}
output "bucket_id" {
  value = aws_s3_bucket.models.id
}
