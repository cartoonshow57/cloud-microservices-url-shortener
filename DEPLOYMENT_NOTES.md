# Deployment Notes

## Cloud Provider
- **Platform**: Microsoft Azure
- **VM Size**: B2ts_v2 (2 vCPU, 1 GB RAM)
- **Region**: West Europe
- **OS**: Ubuntu Server 24.04 LTS

## VM Details
- **VM Name**: url-shortener-vm
- **Public IP**: 20.189.115.187
- **Username**: azureuser
- **SSH Command**: `ssh -i <path-to-key>.pem azureuser@20.189.115.187`

## Important URLs
- **App Health (API)**: http://20.189.115.187/api/health
- **App Health (Redirect)**: http://20.189.115.187/redirect/health
- **Shorten a URL**: `curl -X POST http://20.189.115.187/shorten -H "Content-Type: application/json" -d '{"url":"https://google.com"}'`

## GitHub Actions Secrets (to configure)
| Secret Name        | Value                                      |
|--------------------|--------------------------------------------|
| `AZURE_VM_HOST`    | `20.189.115.187`                           |
| `AZURE_VM_USER`    | `azureuser`                                |
| `AZURE_VM_SSH_KEY` | Contents of your .pem private key file     |

## Status
- [x] Install Docker on the VM
- [x] Clone the GitHub repo on the VM
- [x] Run `docker compose up -d --build` on the VM
- [x] Add GitHub Actions secrets for CI/CD
- [x] Open port 80 in Azure Network Security Group
- [x] App verified publicly accessible
- [ ] Test CI/CD pipeline (push a change and watch GitHub Actions)
- [ ] **DELETE the VM after project submission to avoid charges**

## SSH Alias (local machine)
The SSH config at `~/.ssh/config` has an alias set up:
```
ssh lakshya
```
This connects to the VM without needing to type the full command.
