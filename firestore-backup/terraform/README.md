## Infrastructure set-up with Terraform

> Created with Terraform v0.12.24

- Change all variables in `project.tfvars` file to reflect
your infrastructure setup. If you are starting from scratch,
you will need to create new GCP project and create a bucket
for terraform states in that project. You will also need to
create service account key for the default service account and
store it as `default_service_account.json`. Terraform will use
this account and bucket to perform the operations. For simplicity
you can give it `owner` role so it can perform all operations.

- Change bucket name in `init.tf` to your bucket name.

- Run `terraform init` to see if you have set up everything correctly.

- Run `terraform plan -var-file=project.tfvars -o plan.o` and `terraform apply plan.o`
  possibly multiple times as some resources are dependant on others and
  their creation may fail.

### Terraform configuration

- `apis.tf` - GCP APIs setup
- `build.tf` - cloud build configuration
- `iam.tf` - access control, iam setup
- `init.tf` - project definition, terraform state bucket and providers
- `scheduler.tf` - cloud scheduler configuration
- `storage.tf` - storage bucket for backups
