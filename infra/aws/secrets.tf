resource "random_password" "db_password" {
  length  = 32
  special = false
}

resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

resource "random_id" "workos_cookie_password" {
  byte_length = 32
}

resource "aws_secretsmanager_secret" "app_env" {
  name                    = "${local.name_prefix}/app-env"
  recovery_window_in_days = 0
}

locals {
  api_base_url = "http://${aws_lb.api.dns_name}"
  app_base_url = var.frontend_public_url != "" ? trimsuffix(var.frontend_public_url, "/") : local.api_base_url
  database_url = format(
    "postgresql+psycopg2://%s:%s@%s:%s/%s",
    var.db_username,
    random_password.db_password.result,
    aws_db_instance.postgres.address,
    aws_db_instance.postgres.port,
    var.db_name,
  )
  redis_url = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/0"

  app_secret_defaults = {
    AICREDITS_BASE_URL                             = "https://api.aicredits.in/v1"
    AICREDITS_GENERATION_API_KEY                   = ""
    AICREDITS_GENERATION_BACKOFF_SECONDS           = "1"
    AICREDITS_GENERATION_MAX_ACTIVE_JOBS           = "3"
    AICREDITS_GENERATION_MAX_CONCURRENCY           = "3"
    AICREDITS_GENERATION_MAX_RETRIES               = "2"
    AICREDITS_GENERATION_MAX_TOKENS                = "1600"
    AICREDITS_GENERATION_MODEL_FALLBACK            = "gpt-4o-mini"
    AICREDITS_GENERATION_MODEL_PRIMARY             = "gpt-4o-mini"
    AICREDITS_INTERVIEW_REFINEMENT_API_KEY         = ""
    AICREDITS_INTERVIEW_REFINEMENT_BACKOFF_SECONDS = "1"
    AICREDITS_INTERVIEW_REFINEMENT_MAX_CONCURRENCY = "2"
    AICREDITS_INTERVIEW_REFINEMENT_MAX_RETRIES     = "2"
    AICREDITS_INTERVIEW_REFINEMENT_MAX_TOKENS      = "900"
    AICREDITS_INTERVIEW_REFINEMENT_MODEL_FALLBACK  = "gpt-4o-mini"
    AICREDITS_INTERVIEW_REFINEMENT_MODEL_PRIMARY   = "gpt-4o-mini"
    AICREDITS_INTERVIEW_REFINEMENT_PER_USER_LIMIT  = "16"
    AICREDITS_INTERVIEW_REFINEMENT_WINDOW_SECONDS  = "60"
    AICREDITS_QUESTION_REGEN_API_KEY               = ""
    AICREDITS_QUESTION_REGEN_BACKOFF_SECONDS       = "1"
    AICREDITS_QUESTION_REGEN_MAX_CONCURRENCY       = "2"
    AICREDITS_QUESTION_REGEN_MAX_RETRIES           = "2"
    AICREDITS_QUESTION_REGEN_MAX_TOKENS            = "900"
    AICREDITS_QUESTION_REGEN_MODEL_FALLBACK        = "gpt-4o-mini"
    AICREDITS_QUESTION_REGEN_MODEL_PRIMARY         = "gpt-4o-mini"
    AICREDITS_QUESTION_REGEN_PER_USER_LIMIT        = "8"
    AICREDITS_QUESTION_REGEN_WINDOW_SECONDS        = "60"
    AICREDITS_REPORT_CHAT_API_KEY                  = ""
    AICREDITS_REPORT_CHAT_BACKOFF_SECONDS          = "1"
    AICREDITS_REPORT_CHAT_MAX_ACTIVE_PER_USER      = "1"
    AICREDITS_REPORT_CHAT_MAX_CONCURRENCY          = "2"
    AICREDITS_REPORT_CHAT_MAX_RETRIES              = "3"
    AICREDITS_REPORT_CHAT_MAX_TOKENS               = "700"
    AICREDITS_REPORT_CHAT_MODEL_FALLBACK           = "gpt-4o-mini"
    AICREDITS_REPORT_CHAT_MODEL_PRIMARY            = "gpt-4o-mini"
    AICREDITS_REPORT_CHAT_PER_USER_LIMIT           = "12"
    AICREDITS_REPORT_CHAT_WINDOW_SECONDS           = "60"
    APP_ENV                                        = "production"
    CELERY_QUEUE_DEFAULT                           = "default"
    CELERY_QUEUE_GENERATION                        = "generation"
    CELERY_QUEUE_MAINTENANCE                       = "maintenance"
    CELERY_QUEUE_PROCESSING                        = "processing"
    CELERY_TASK_ALWAYS_EAGER                       = "false"
    CELERY_TASK_EAGER_PROPAGATES                   = "true"
    CELERY_TASK_SOFT_TIME_LIMIT_SECONDS            = "540"
    CELERY_TASK_TIME_LIMIT_SECONDS                 = "600"
    CELERY_WORKER_PREFETCH_MULTIPLIER              = "1"
    CSRF_COOKIE_NAME                               = "agis_csrf"
    CSRF_HEADER_NAME                               = "X-CSRF-Token"
    DB_MAX_OVERFLOW                                = "10"
    DB_POOL_SIZE                                   = "5"
    DEV_BOOTSTRAP_ADMIN                            = "false"
    ENABLE_BACKGROUND_WORKERS                      = "false"
    ENABLE_BEARER_TOKEN_AUTH                       = "false"
    FOUNDER_ADMIN_EMAIL                            = "admin@example.com"
    INTERVIEW_REFINEMENT_MAX_INSTRUCTION_CHARS     = "200"
    INTERVIEW_REFINEMENT_MAX_TEXT_CHARS            = "4000"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES                = "60"
    JWT_ALGORITHM                                  = "HS256"
    LANGFUSE_CAPTURE_IO                            = "false"
    LANGFUSE_ENABLED                               = "false"
    LANGFUSE_HOST                                  = ""
    LANGFUSE_PUBLIC_KEY                            = ""
    LANGFUSE_SECRET_KEY                            = ""
    LLM_DISABLE_LIVE_CALLS                         = "false"
    LLM_ENDPOINT                                   = "https://api.aicredits.in/v1/chat/completions"
    LLM_JSON_MODE                                  = "true"
    LLM_MODEL_NAME                                 = "gpt-4o-mini"
    LLM_PAYLOAD_MODE                               = "full"
    LLM_PROVIDER                                   = "aicredits"
    LLM_TEMPERATURE                                = "0.0"
    LLM_TIMEOUT_SECONDS                            = "120"
    LOG_LEVEL                                      = "INFO"
    MAX_PROFILE_IMAGE_SIZE_MB                      = "5"
    MAX_UPLOAD_SIZE_MB                             = "10"
    OBSERVABILITY_ENABLED                          = "false"
    OBSERVABILITY_EXPORTER                         = "otlp"
    OTEL_DEPLOYMENT_ENVIRONMENT                    = "production"
    OTEL_EXPORTER_OTLP_ENDPOINT                    = ""
    OTEL_EXPORTER_OTLP_HEADERS                     = ""
    OTEL_EXPORTER_OTLP_PROTOCOL                    = "http/protobuf"
    OTEL_SERVICE_NAME                              = "ag-interview-standardiser"
    PARSER_ENGINE_VERSION                          = "v2"
    PROCESSING_JOB_BACKOFF_SECONDS                 = "5"
    PROCESSING_JOB_MAX_ATTEMPTS                    = "3"
    PROCESSING_JOB_STALE_AFTER_SECONDS             = "300"
    PROCESSING_WORKER_POLL_SECONDS                 = "2"
    QDRANT_API_KEY                                 = ""
    QDRANT_COLLECTION                              = "agis_question_versions"
    QDRANT_DISABLE                                 = "true"
    QDRANT_TIMEOUT_SECONDS                         = "5"
    QDRANT_URL                                     = ""
    RAG_CANDIDATE_LIMIT                            = "15"
    RAG_EMBEDDING_DIMENSION                        = "384"
    RAG_EMBEDDING_MODEL                            = "BAAI/bge-small-en-v1.5"
    RAG_RETRIEVAL_LIMIT                            = "3"
    REDIS_CONNECT_TIMEOUT_SECONDS                  = "2"
    REDIS_KEY_PREFIX                               = local.name_prefix
    REPORT_CHAT_MAX_QUESTION_CHARS                 = "500"
    REPORT_CHAT_MAX_QUESTION_WORDS                 = "80"
    SESSION_COOKIE_NAME                            = "agis_session"
    SESSION_COOKIE_SAMESITE                        = "lax"
    STORAGE_BACKEND                                = "s3"
    TRUST_X_FORWARDED_FOR                          = "false"
    TRUSTED_PROXY_IPS                              = ""
    UPLOAD_DIRECTORY                               = "/app/uploads"
    WORKOS_API_KEY                                 = ""
    WORKOS_CLIENT_ID                               = ""
    WORKOS_LOGOUT_REDIRECT_URI                     = local.app_base_url
    WORKOS_REDIRECT_URI                            = "${local.app_base_url}/api/auth/callback"
  }

  app_secret_managed_values = {
    API_DOMAIN             = aws_lb.api.dns_name
    AWS_REGION             = var.aws_region
    BACKEND_API_URL        = local.api_base_url
    CELERY_BROKER_URL      = local.redis_url
    CELERY_RESULT_BACKEND  = local.redis_url
    CORS_ALLOWED_ORIGINS   = local.app_base_url
    CSRF_TRUSTED_ORIGINS   = local.app_base_url
    DATABASE_URL           = local.database_url
    FRONTEND_ORIGIN        = local.app_base_url
    JWT_SECRET             = random_password.jwt_secret.result
    REDIS_URL              = local.redis_url
    S3_BUCKET              = aws_s3_bucket.assets.bucket
    S3_PREFIX              = local.normalized_s3_prefix
    TRUSTED_HOSTS          = aws_lb.api.dns_name
    WORKOS_COOKIE_PASSWORD = replace(replace(random_id.workos_cookie_password.b64_std, "+", "-"), "/", "_")
  }

  app_secret_values = merge(
    local.app_secret_defaults,
    var.app_secret_overrides,
    local.app_secret_managed_values,
  )

  app_secret_names = sort(keys(merge(local.app_secret_defaults, local.app_secret_managed_values)))
  ecs_app_secrets = [
    for name in local.app_secret_names : {
      name      = name
      valueFrom = "${aws_secretsmanager_secret.app_env.arn}:${name}::"
    }
  ]
}

resource "aws_secretsmanager_secret_version" "app_env" {
  secret_id     = aws_secretsmanager_secret.app_env.id
  secret_string = jsonencode(local.app_secret_values)
}
