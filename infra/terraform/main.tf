# Описание стенда. 
#
# Стенд — это замена арендованным машинам. Здесь создаются сеть, хранилище,
# база данных и «серверы»: контейнеры с установленным ssh, к которым
# сценарий настройки подключается как к обычным машинам.
#
# Команды:
#   tofu init      подготовить рабочий каталог, скачать дополнение
#   tofu plan      показать, что изменится, ничего не меняя
#   tofu apply     привести стенд к описанному виду
#   tofu destroy   удалить всё описанное здесь
#
# Вместо tofu можно писать terraform — язык описания одинаковый.

terraform {
  required_version = ">= 1.10"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }

  # ЗАДАНИЕ: включите хранение файла состояния отдельно
  # от вашей машины. Пока этот блок закомментирован, состояние лежит
  # рядом с описанием, и одновременная работа двоих ломает стенд —
  # 
  #
  # backend "s3" {
  #   bucket                      = "praktikum-state"
  #   key                         = "stand/terraform.tfstate"
  #   endpoints                   = { s3 = "http://localhost:9000" }
  #   region                      = "ru-central1"
  #   skip_credentials_validation = true
  #   skip_region_validation      = true
  #   skip_requesting_account_id  = true
  #   skip_s3_checksum            = true
  #   use_path_style              = true
  #   use_lockfile                = true
  # }
}

provider "docker" {}

# ---------------------------------------------------------------------------
# Сеть и хранилище
# ---------------------------------------------------------------------------

resource "docker_network" "stand" {
  name = "${var.project_name}-net"
}

resource "docker_volume" "pgdata" {
  name = "${var.project_name}-pgdata"
}

# ---------------------------------------------------------------------------
# База данных
# ---------------------------------------------------------------------------

resource "docker_image" "postgres" {
  name         = "postgres:16-alpine"
  keep_locally = true
}

resource "docker_container" "db" {
  name  = "${var.project_name}-db"
  image = docker_image.postgres.image_id

  env = [
    "POSTGRES_USER=${var.db_user}",
    "POSTGRES_PASSWORD=${var.db_password}",
    "POSTGRES_DB=${var.db_name}",
  ]

  networks_advanced {
    name = docker_network.stand.name
  }

  volumes {
    volume_name    = docker_volume.pgdata.name
    container_path = "/var/lib/postgresql/data"
  }

  ports {
    internal = 5432
    external = var.db_port
    ip       = "127.0.0.1"
  }

  restart = "unless-stopped"
}

# ---------------------------------------------------------------------------
# «Серверы»
#
# Обычные машины с точки зрения сценария настройки: ssh, пользователь,
# каталоги. Приложение туда ставится пакетом, а не образом, — и это
# отдельный урок о том, что происходит внутри контейнера.
# ---------------------------------------------------------------------------

resource "docker_image" "server" {
  name = "${var.project_name}-server"

  build {
    context = "${path.module}/../server-image"
    build_args = {
      SSH_PUBLIC_KEY = trimspace(file(pathexpand(var.ssh_public_key_path)))
    }
  }
}

resource "docker_container" "server" {
  count = var.server_count

  name  = "${var.project_name}-server-${count.index + 1}"
  image = docker_image.server.image_id

  networks_advanced {
    name = docker_network.stand.name
  }

  # Каждому серверу свой порт для входа: 2201, 2202, …
  ports {
    internal = 22
    external = var.ssh_base_port + count.index
    ip       = "127.0.0.1"
  }

  # Порт приложения: 8101, 8102, …
  ports {
    internal = 8000
    external = var.app_base_port + count.index
    ip       = "127.0.0.1"
  }

  restart = "unless-stopped"
}
