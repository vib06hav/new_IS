param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("current", "upgrade", "downgrade", "history", "heads")]
    [string]$Command,

    [string]$Revision = "head"
)

$ErrorActionPreference = "Stop"

switch ($Command) {
    "upgrade" {
        docker compose run --rm --no-deps api alembic upgrade $Revision
    }
    "downgrade" {
        docker compose run --rm --no-deps api alembic downgrade $Revision
    }
    "current" {
        docker compose run --rm --no-deps api alembic current
    }
    "history" {
        docker compose run --rm --no-deps api alembic history
    }
    "heads" {
        docker compose run --rm --no-deps api alembic heads
    }
}
