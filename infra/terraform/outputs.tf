# Что описание отдаёт наружу после применения.
# Посмотреть: tofu output
#
# Главный смысл этого файла: отсюда адреса «серверов»
# будут сами попадать в список серверов для сценария настройки, и никто
# больше не будет вписывать их руками.

output "database_url" {
  description = "Готовая строка подключения к базе данных стенда"
  value       = "postgresql+psycopg://${var.db_user}:${var.db_password}@localhost:${var.db_port}/${var.db_name}"
  sensitive   = true
}

output "servers" {
  description = "Учебные «серверы»: имя, порт для входа и порт приложения"
  value = [
    for index, container in docker_container.server : {
      name     = container.name
      ssh_port = var.ssh_base_port + index
      app_port = var.app_base_port + index
    }
  ]
}

output "ansible_inventory" {
  description = "Inventory для Ansible из фактических портов серверов"
  value = join("\n", concat(
    ["[app]"],
    [for index, container in docker_container.server :
      "${container.name} ansible_host=127.0.0.1 ansible_port=${var.ssh_base_port + index} ansible_user=deploy"
    ],
    [""]
  ))
}
