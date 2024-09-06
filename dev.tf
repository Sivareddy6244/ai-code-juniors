module "google_service_account_creation" {
    source = "../modules/service-account"
    project_id = "cedar-context-433909-d9"
    project_number = "750473332715"
    service_account_email_id = "composer-actual-service-account"
  
}

module "google_composer_environment" {
    source = "../modules/composer"
    project_id = "cedar-context-433909-d9"
    project_number = "750473332715"
    composer_name = "terraform-composer"
    composer_image_version = "composer-2-airflow-2"
    
    composer_storage_bucket_name = "composer-bucket476800"
    region    = "us-central1"

    service_account_email_id = "composer-actual-service-account"
