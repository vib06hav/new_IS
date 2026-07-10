resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_task_cpu
  memory                   = var.api_task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_app_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = local.backend_image
      essential = true

      portMappings = [
        {
          containerPort = var.api_container_port
          hostPort      = var.api_container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "STORAGE_BACKEND"
          value = "s3"
        },
        {
          name  = "S3_BUCKET"
          value = aws_s3_bucket.assets.bucket
        },
        {
          name  = "S3_PREFIX"
          value = local.normalized_s3_prefix
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "api"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_task_cpu
  memory                   = var.worker_task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_app_task.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = local.backend_image
      essential = true
      command = [
        "celery",
        "-A",
        "app.tasks.celery_app.celery_app",
        "worker",
        "--loglevel=INFO",
        "--queues=processing,generation,maintenance,default"
      ]

      environment = [
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "STORAGE_BACKEND"
          value = "s3"
        },
        {
          name  = "S3_BUCKET"
          value = aws_s3_bucket.assets.bucket
        },
        {
          name  = "S3_PREFIX"
          value = local.normalized_s3_prefix
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "worker"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "migration" {
  family                   = "${local.name_prefix}-migration"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_app_task.arn

  container_definitions = jsonencode([
    {
      name      = "migration"
      image     = local.backend_image
      essential = true
      command   = ["alembic", "upgrade", "head"]

      environment = [
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "STORAGE_BACKEND"
          value = "s3"
        },
        {
          name  = "S3_BUCKET"
          value = aws_s3_bucket.assets.bucket
        },
        {
          name  = "S3_PREFIX"
          value = local.normalized_s3_prefix
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.migration.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "migration"
        }
      }
    }
  ])
}
