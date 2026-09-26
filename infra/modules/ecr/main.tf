resource "aws_ecr_repository" "this" {
  for_each = var.repositories

  name                 = "${var.project_name}-${each.key}"
  image_tag_mutability = "IMMUTABLE" # a tag (git SHA) always means the same image

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "this" {
  for_each   = aws_ecr_repository.this
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the last ${var.images_to_keep} images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = var.images_to_keep
      }
      action = { type = "expire" }
    }]
  })
}

# Role that GitHub Actions assumes via OIDC to push images.
data "aws_iam_policy_document" "push_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Pushes only from these branches, never from PRs or other branches.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        for b in var.push_branches :
        "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/${b}"
      ]
    }
  }
}

resource "aws_iam_role" "push" {
  name               = "${var.project_name}-github-actions-ecr-push"
  assume_role_policy = data.aws_iam_policy_document.push_trust.json
}

data "aws_iam_policy_document" "push" {
  # The login token call can't be scoped to a repository.
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
    ]
    resources = [for r in aws_ecr_repository.this : r.arn]
  }
}

resource "aws_iam_role_policy" "push" {
  name   = "ecr-push"
  role   = aws_iam_role.push.id
  policy = data.aws_iam_policy_document.push.json
}