# AX Merchant Portal - Vercel Deployment Guide

## 📋 Prerequisites

- Vercel account (sign up at https://vercel.com)
- GitHub repository: https://github.com/LibertytechX/aexpress.git
- Backend already deployed at: https://www.orders.axpress.net

---

## 🚀 Deployment Steps

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/new
   - Sign in with your GitHub account

2. **Import Git Repository**
   - Click "Add New..." → "Project"
   - Select "Import Git Repository"
   - Choose: `LibertytechX/aexpress`
   - Click "Import"

3. **Configure Project**
   - **Framework Preset**: Other (or None)
   - **Root Directory**: `frontend` (IMPORTANT!)
   - **Build Command**: Leave empty (static site)
   - **Output Directory**: Leave empty (uses root)
   - **Install Command**: Leave empty (no build needed)

4. **Environment Variables**
   - No environment variables needed (API URL is hardcoded)

5. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete (usually 1-2 minutes)

---

### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy from frontend directory**
   ```bash
   cd frontend
   vercel --prod
   ```

4. **Follow the prompts**
   - Set up and deploy? Yes
   - Which scope? Select your account
   - Link to existing project? No
   - Project name? ax-merchant-portal
   - In which directory is your code located? ./
   - Want to override settings? No

---

## 🔧 Post-Deployment Configuration

### 1. Update Backend CORS Settings

After deployment, you'll get a Vercel URL like: `https://ax-merchant-portal.vercel.app`

**Update the backend .env file:**

```bash
ssh root@144.126.208.115
nano /home/backend/.env
```

**Add your Vercel URL:**
```
FRONTEND_URL=https://your-vercel-app.vercel.app
```

**Restart the backend:**
```bash
systemctl restart axpress-api
```

### 2. Test the Deployment

Visit your Vercel URL and test:
- ✅ Login page loads
- ✅ Can register new user
- ✅ Can login
- ✅ Dashboard loads
- ✅ Can create orders
- ✅ Wallet functions work

---

## 📁 Files Included in Deployment

The following files will be deployed to Vercel:

```
frontend/
├── index.html          # Main HTML file
├── MerchantPortal.jsx  # React components
├── api.js              # API service (points to production backend)
├── vercel.json         # Vercel configuration
└── README.md           # Documentation
```

---

## 🌐 Custom Domain (Optional)

### Add Custom Domain to Vercel:

1. Go to your project in Vercel Dashboard
2. Click "Settings" → "Domains"
3. Add your custom domain (e.g., `portal.axpress.net`)
4. Follow DNS configuration instructions
5. Update backend CORS with new domain

---

## 🔍 Troubleshooting

### Issue: CORS Errors

**Solution**: Make sure backend .env has your Vercel URL:
```bash
ssh root@144.126.208.115 'cat /home/backend/.env | grep FRONTEND_URL'
```

### Issue: API Calls Failing

**Solution**: Check that API_BASE_URL in api.js is correct:
```javascript
const API_BASE_URL = 'https://www.orders.axpress.net/api';
```

### Issue: 404 on Refresh

**Solution**: Vercel.json is configured to handle SPA routing. If issues persist, check vercel.json configuration.

---

## ✅ Deployment Checklist

- [ ] Vercel account created
- [ ] Repository imported to Vercel
- [ ] Root directory set to `frontend`
- [ ] Deployment successful
- [ ] Frontend loads in browser
- [ ] Backend CORS updated with Vercel URL
- [ ] Login/Register tested
- [ ] Dashboard tested
- [ ] Order creation tested
- [ ] Wallet functions tested

---

## 📞 Support

**Backend API**: https://www.orders.axpress.net  
**Repository**: https://github.com/LibertytechX/aexpress.git  
**Admin Email**: admin@axpress.net

---

**Happy Deploying! 🚀**

