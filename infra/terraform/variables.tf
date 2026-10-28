# Значения, которые могут отличаться у разных пар.
# Пароль здесь учебный и нужен только на своей машине. Настоящие пароли

variable "project_name" {
  description = "Приставка в именах создаваемых объектов"
  type        = string
  default     = "praktikum"
}

variable "ssh_public_key_path" {
  description = "Путь к вашему открытому ключу — он кладётся на «серверы»"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "server_count" {
  description = "Сколько учебных «серверов» поднимать"
  type        = number
  default     = 2

  validation {
    condition     = var.server_count >= 1 && var.server_count <= 10 && floor(var.server_count) == var.server_count
    error_message = "Число серверов должно быть целым от 1 до 10."
  }
}

variable "ssh_base_port" {
  description = "Первый порт для входа на «серверы»: 2201, 2202, …"
  type        = number
  default     = 2201
}

variable "app_base_port" {
  description = "Первый порт приложения на «серверах»: 8101, 8102, …"
  type        = number
  default     = 8101
}

variable "db_user" {
  description = "Пользователь базы данных"
  type        = string
  default     = "praktikum"
}

variable "db_password" {
  description = "Пароль базы данных (учебный, только для стенда)"
  type        = string
  default     = "praktikum"
  sensitive   = true
}

variable "db_name" {
  description = "Имя базы данных"
  type        = string
  default     = "accounts"
}

variable "db_port" {
  description = "Порт, на котором база данных видна на вашей машине"
  type        = number
  default     = 5432
}
