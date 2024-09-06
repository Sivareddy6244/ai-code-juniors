provider "google" {
  project = var.project_id
}

# Create the storage bucket
resource "google_storage_bucket" "storage_bucket" {
  name                        = var.composer_storage_bucket_name
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = false
  public_access_prevention    = "enforced"
}

# Update the Composer environment to use the new service account
resource "google_composer_environment" "test" {
  name   = var.composer_name
  region = var.region

  storage_config {
    bucket = "gs://${var.composer_storage_bucket_name}"
  }

  config {
    software_config {
      image_version = var.composer_image_version
    }

    workloads_config {
      scheduler {
        count      = 2
        cpu        = 1
        memory_gb  = 2
        storage_gb = 1
      }

      triggerer {
        count      = 2
        cpu        = 0.5
        memory_gb  = 0.5
      }

      web_server {
        cpu        = 0.5
        memory_gb  = 2
        storage_gb = 1
      }

      worker {
        min_count  = 8
        max_count  = 16
        cpu        = 4
        memory_gb  = 8
        storage_gb = 4
      }
    }

    environment_size = "ENVIRONMENT_SIZE_MEDIUM"

    private_environment_config {
      enable_private_endpoint = true
    }

    node_config {
      network                = "projects/${var.project_id}/global/networks/${var.network_name}"
      service_account        = "${var.service_account_email_id}@${var.project_id}.iam.gserviceaccount.com"
      subnetwork             = "projects/${var.project_id}/regions/${var.subnet_region}/subnetworks/${var.subnetwork}"

      # Uncomment and configure the IP allocation policy if needed
      # ip_allocation_policy {
      #   cluster_secondary_range_name = var.subnetwork_pod_range_name
      #   services_secondary_range_name = var.subnetwork_svc_range_name
      # }
    }
  }
}
-------------------------------------------------------------------------------------------------------------------

      variable "project_id" {
  description = "The ID of the Google Cloud project."
  type        = string
  default = "cedar-context-433909-d9"
}

variable "project_number" {
  type = string
  default = "750473332715"
  
}

variable "composer_storage_bucket_name" {
  description = "The name of the Cloud Storage bucket for Composer."
  type        = string
  default = "composer-bucket-siva62440817"
}

variable "region" {
  description = "The region where resources will be created."
  type        = string
  default = "us-central1"
}

variable "composer_name" {
  description = "The name of the Composer environment."
  type        = string
  default = "terraform-composer"
}

variable "composer_image_version" {
  description = "The image version of the Composer environment."
  type        = string
  default = "composer-2-airflow-2"
}

variable "network_name" {
  description = "The name of the network for the Composer environment."
  type        = string
  default     = "default"
}


variable "subnet_region" {
  description = "The region where the subnet is located."
  type        = string
  default = "us-central1"
}

variable "subnetwork" {
  description = "The name of the subnetwork for the Composer environment."
  type        = string
  default = "default"
}

variable "subnetwork_pod_range_name" {
  description = "The name of the secondary IP range for pods."
  type        = string
  default = "default"
  
}

variable "subnetwork_svc_range_name" {
  description = "The name of the secondary IP range for services."
  type        = string
  default = "default"
}


variable "service_account_email_id" {
  description = "The email ID of the service account."
  type        = string
  default = "composer-actual-service-account"
}
--------------------------------------------------------------------------------------------------------------------------------------

  service




  provider "google" {
  project = var.project_id
}

# Create a new service account
resource "google_service_account" "new_composer_sa" {
  account_id   = var.service_account_email_id
  display_name = "New Service Account for Composer Environment"
}

# Assign the roles/composer.worker role to the new service account
resource "google_project_iam_member" "composer_worker_role" {
  project = var.project_id
  role    = "roles/composer.worker"
  member  = "serviceAccount:${google_service_account.new_composer_sa.email}"
}

# Assign the roles/composer.ServiceAgentV2Ext role to the Composer service account
resource "google_service_account_iam_member" "composer_service_agent_role" {
  provider = google-beta
  service_account_id = "${var.service_account_email_id}@${var.project_id}.iam.gserviceaccount.com"
  role = "roles/composer.ServiceAgentV2Ext"
  member = "serviceAccount:service-${var.project_number}@cloudcomposer-accounts.iam.gserviceaccount.com"
}
-----------------------------------------------------------------------

  variable "project_id" {
  description = "The ID of the Google Cloud project."
  type        = string
  default = "cedar-context-433909-d9"
}

variable "project_number" {
  type = string
  default = "750473332715"
  
}


variable "service_account_email_id" {
  description = "The email ID of the service account."
  type        = string
  default = "composer-actual-service-account"
}
