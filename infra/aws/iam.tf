data "aws_iam_policy_document" "ecs_tasks_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${local.name_prefix}-ecs-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_app_task" {
  name               = "${local.name_prefix}-ecs-app-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
}

data "aws_iam_policy_document" "app_s3_access" {
  statement {
    sid = "ListAssetsBucketPrefix"

    actions = [
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.assets.arn,
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${local.normalized_s3_prefix}/*"]
    }
  }

  statement {
    sid = "ReadWriteAssetsPrefix"

    actions = [
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:PutObject",
    ]

    resources = [
      "${aws_s3_bucket.assets.arn}/${local.normalized_s3_prefix}/*",
    ]
  }
}

resource "aws_iam_policy" "app_s3_access" {
  name        = "${local.name_prefix}-app-s3-access"
  description = "Allow the AGIS ECS task role to read/write only the application asset prefix."
  policy      = data.aws_iam_policy_document.app_s3_access.json
}

resource "aws_iam_role_policy_attachment" "app_s3_access" {
  role       = aws_iam_role.ecs_app_task.name
  policy_arn = aws_iam_policy.app_s3_access.arn
}
