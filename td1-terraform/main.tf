terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_image" "catalog" {
  name         = "nginxdemos/hello:latest"
  keep_locally = true
}

resource "docker_container" "catalog" {
  name  = "catalog-terraform"
  image = docker_image.catalog.image_id

  ports {
    internal = 80
    external = 8081
  }
}
