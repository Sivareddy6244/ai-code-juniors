# Define a custom IAM role
resource "google_project_iam_custom_role" "bigquery_custom_role" {
  role_id     = "bigquery_custom_role"  # Role ID
  title       = "BigQuery Custom Role"
  description = "My custom IAM role"
  permissions = [
    "bigquery.tables.create"
  ]
}

# Use a module to manage IAM role bindings
module "base-roles" {
  source = "git::https://gitlab.kazan.myworldline.com/ccc/terraform/modules/gcp/base-roles.git"

  object_code = var.object_code
  project     = local.project_id

  custom_role_bindings = {
    "projects/${local.project_id}/roles/bigquery_custom_role" = [
      "group:dl-cmdb-limosa-futuro-poc-developer@worldline.com"
    ]
  }

  exclude_bindings = {
    "developer" = [
      "roles/storage.objectAdmin",
      "roles/bigquery.admin",
      "roles/storage.admin",
      "roles/bigquery.dataEditor"
    ]
  }
}
