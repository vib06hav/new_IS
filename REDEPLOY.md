# Redeployment Guide

> Use this every time you buy a new VPS. Takes ~15 minutes.

## Step 1 — Buy a VPS
- Provider: DigitalOcean (Bangalore) or Vultr (Mumbai)
- Specs: 2 vCPU, 4 GB RAM, 40 GB SSD, Ubuntu 22.04
- Add your existing SSH public key (`~/.ssh/digitalocean_agis.pub`) during creation
- Note the new **Public IPv4 address**

---

## Step 2 — Update `.env.production` on your laptop
Change these 3 lines to the new IP:
```
API_DOMAIN=<NEW_IP>
BACKEND_API_URL=http://<NEW_IP>
TRUSTED_HOSTS=<NEW_IP>
```
Everything else stays the same.

---

## Step 3 — Update Vercel
1. Go to Vercel → Project → **Settings → Environment Variables**
2. Edit `BACKEND_API_URL` → set to `http://<NEW_IP>`
3. Go to **Deployments** → Redeploy the latest deployment

> WorkOS does NOT need to change — it points to Vercel, not the IP.

---

## Step 4 — Set up the VPS

Open PowerShell and SSH in:
```powershell
ssh root@<NEW_IP> -i $HOME\.ssh\digitalocean_agis
```

Install Docker:
```bash
curl -fsSL https://get.docker.com | sh
```

Clone the repo:
```bash
git clone https://github.com/vib06hav/new_IS.git /opt/ag-is
cd /opt/ag-is
```

---

## Step 5 — Copy `.env.production` to the server
Open a **new PowerShell window** on your laptop:
```powershell
scp -i $HOME\.ssh\digitalocean_agis "C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\.env.production" root@<NEW_IP>:/opt/ag-is/.env.production
```

---

## Step 6 — Start everything
Back in the SSH window:
```bash
cd /opt/ag-is
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```
Wait 3–5 minutes. Then verify:
```bash
curl http://<NEW_IP>/health
```
Should return `{"status":"ok",...}`.

---

## Step 7 — Test
Open browser → `https://interview-standardiser.vercel.app/admin/login` → try logging in.

---

## Taking it offline
```bash
# Stop (still costs money)
docker compose -f docker-compose.prod.yml down

# To stop paying: delete the VPS from DigitalOcean/Vultr dashboard
```

## Pushing a new feature
```bash
# On laptop
git add . && git commit -m "your message" && git push

# On VPS (SSH in first)
cd /opt/ag-is
git pull origin main
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```
