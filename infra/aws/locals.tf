data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  normalized_s3_prefix = trim(var.s3_prefix, "/")
  backend_image        = "${aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"

  assets_bucket_name = var.s3_bucket_name != "" ? var.s3_bucket_name : lower(
    "${local.name_prefix}-assets-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  )

  common_tags = {
    Project     = "AG Interview Standardiser"
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "Terraform"
  }
}
