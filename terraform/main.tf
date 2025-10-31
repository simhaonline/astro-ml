provider "aws" {
  region = var.region
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "astro-ml"
  cluster_version = "1.30"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    gpu = {
      instance_types = ["g4dn.xlarge"]
      min_size     = 0
      max_size     = 4
      desired_size = 1
      labels = { workload = "training", gpu = "true" }
      taints = [{
        key    = "nvidia.com/gpu"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }
    cpu = {
      instance_types = ["t3.medium"]
      min_size     = 2
      max_size     = 10
      desired_size = 2
    }
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "astro-vpc"
  cidr = "10.0.0.0/16"

  azs             = data.aws_availability_zones.azs.names
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}

data "aws_availability_zones" "azs" {
  state = "available"
}

resource "aws_s3_bucket" "models" {
  bucket = "astro-ml-models-${data.aws_caller_identity.current.account_id}"
}

data "aws_caller_identity" "current" {}
