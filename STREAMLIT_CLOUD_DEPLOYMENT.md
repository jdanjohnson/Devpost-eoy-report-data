# Streamlit Community Cloud vs Google Cloud Run Deployment

## Executive Summary

For **Phase 1** (single-user, private access), **Streamlit Community Cloud** is the recommended deployment path with minimal operational overhead. It provides immediate deployment from GitHub with built-in authentication and zero infrastructure management.

For **Phase 2+** (team-wide access, durable storage, enterprise controls), **Google Cloud Run** provides persistence, scalability, and advanced security options at modest complexity.

---

## Architecture Comparison

### Streamlit Community Cloud Architecture

**Components:**
- **Source**: Deploys directly from GitHub repository and branch
- **Runtime**: Managed Streamlit container (Python 3.9+)
- **Compute**: Shared compute resources (suitable for single-user demos)
- **Storage**: Local filesystem inside app container (ephemeral)
- **Database**: SQLite stored in container filesystem
- **Secrets**: Managed via Streamlit Cloud Secrets (encrypted at rest)
- **Access Control**: Private app with invite-based access (Streamlit accounts)
- **Networking**: HTTPS via Streamlit Cloud domain (*.streamlit.app)

**Data Flow:**
```
User Browser (HTTPS)
    ↓
Streamlit Cloud Container
    ↓
Local Filesystem (/app, /tmp)
    ↓
In-Memory Processing (pandas, plotly)
    ↓
Stream to Browser (downloads)
```

### Google Cloud Run Architecture

**Components:**
- **Compute**: Cloud Run (serverless containers, auto-scaling)
- **Storage**: Cloud Storage bucket mounted via Cloud Storage FUSE
- **Database**: SQLite (stored in Cloud Storage bucket)
- **Container**: Docker image with Streamlit + Python dependencies
- **Networking**: Private Cloud Run service (requires IAM authentication)
- **Access Control**: IAM/OIDC with optional VPC, Cloud Armor, custom domain
- **Monitoring**: Cloud Logging, Cloud Monitoring, alerting

**Data Flow:**
```
User Browser (HTTPS)
    ↓
Cloud Run Instance
    ↓
Cloud Storage Bucket (mounted via FUSE)
    ↓
Process & Store Parquet Files
    ↓
Generate Reports → Store in Cloud Storage
    ↓
Download to Browser
```

---

## Data Storage & Retention

### Streamlit Community Cloud

**At Rest:**
- Files written to container filesystem (`/app` or `/tmp`)
- **Persistence**: Files typically persist between app restarts but are **not guaranteed** across redeploys or image rebuilds
- **No durable storage** by default - ephemeral by design
- **Encryption**: Managed by Streamlit Cloud infrastructure (encrypted at rest)

**In Transit:**
- HTTPS/TLS encryption for all connections
- Secure WebSocket connections for Streamlit sessions

**Data Retention Policy:**
- **Uploaded Files**: Stored temporarily in container filesystem; cleared on redeploy
- **Processed Data**: Parquet files stored in container; cleared on redeploy
- **Job History**: SQLite database in container; cleared on redeploy
- **Exports**: Generated on-demand and streamed to browser; not retained on server
- **Source Data**: `hackathons_source.xlsx` committed to private GitHub repo (403KB)

**Who Has Access:**
- Only invited Streamlit accounts can access the app
- App owners can view server logs (avoid logging sensitive content)
- Streamlit Cloud infrastructure team (for platform maintenance)

**Recommendation for "No Retention" Posture:**
- Use `/tmp` directory for all temporary files
- Delete files immediately after processing
- Stream exports from memory (`BytesIO`) instead of writing to disk
- Disable or minimize job history persistence
- Provide "Purge All Data" button for manual cleanup

### Google Cloud Run

**At Rest:**
- Durable storage in Google Cloud Storage (GCS)
- **Persistence**: Explicit and durable until manually deleted
- **Encryption**: Encrypted at rest (Google-managed or customer-managed keys)
- **Lifecycle**: Configurable retention policies and auto-delete rules

**In Transit:**
- HTTPS/TLS encryption via Cloud Run
- Private networking options (VPC, Cloud Interconnect)

**Data Retention Policy:**
- **Uploaded Files**: Stored in GCS bucket; retained until explicitly deleted
- **Processed Data**: Parquet files in GCS; retained per lifecycle policy
- **Job History**: SQLite in GCS; durable and backed up
- **Exports**: Stored in GCS output directory; retained per policy
- **Source Data**: `hackathons_source.xlsx` in GCS or container image

**Who Has Access:**
- IAM-controlled access (service accounts, user accounts)
- VPC Service Controls for network isolation
- Cloud Audit Logs for access tracking
- Optional: Cloud Armor for DDoS protection

---

## Security Comparison

### Streamlit Community Cloud

**Authentication:**
- ✅ Private app with invite-based access
- ✅ Streamlit account authentication (email-based)
- ❌ No custom SSO/SAML integration
- ❌ No multi-factor authentication (MFA) enforcement

**Authorization:**
- ✅ App-level access control (all invited users have full access)
- ❌ No role-based access control (RBAC)
- ❌ No granular permissions

**Data Security:**
- ✅ HTTPS/TLS for all connections
- ✅ Secrets management (encrypted at rest)
- ✅ XSRF protection enabled by default
- ⚠️ Shared compute environment (multi-tenant)
- ⚠️ No network isolation options

**Compliance:**
- ⚠️ Limited compliance certifications
- ⚠️ No HIPAA/SOC 2 guarantees for Community tier
- ⚠️ Data residency not configurable

**Best Practices:**
- Enforce file size/type validation on uploads
- Sanitize ZIP extraction (Zip Slip protection)
- Avoid logging sensitive data or PII
- Use Streamlit Secrets for API keys/credentials
- Implement app-level "no retention" controls
- Provide clear UI messaging about data handling

### Google Cloud Run

**Authentication:**
- ✅ IAM-based authentication
- ✅ OIDC/OAuth 2.0 support
- ✅ Custom SSO/SAML integration
- ✅ MFA enforcement via Google Workspace

**Authorization:**
- ✅ IAM roles and permissions
- ✅ Service account-based access
- ✅ Fine-grained access control
- ✅ VPC Service Controls

**Data Security:**
- ✅ HTTPS/TLS for all connections
- ✅ Private endpoints (no public internet exposure)
- ✅ VPC networking and firewall rules
- ✅ Cloud Armor for DDoS/WAF protection
- ✅ Customer-managed encryption keys (CMEK)
- ✅ Dedicated compute (no multi-tenancy concerns)

**Compliance:**
- ✅ SOC 2, ISO 27001, HIPAA, PCI DSS
- ✅ Data residency controls (regional deployment)
- ✅ Cloud Audit Logs for compliance tracking
- ✅ Data Loss Prevention (DLP) integration

**Best Practices:**
- Use private Cloud Run services (no public access)
- Implement least-privilege IAM roles
- Enable Cloud Logging and Monitoring
- Set up lifecycle policies for auto-delete
- Use VPC Service Controls for network isolation
- Implement Cloud Armor rules for additional protection

---

## Operational Comparison

| Feature | Streamlit Cloud | Google Cloud Run |
|---------|----------------|------------------|
| **Setup Time** | 5-10 minutes | 1-2 hours |
| **Deployment** | One-click from GitHub | Docker build + push + deploy |
| **Scaling** | Automatic (limited resources) | Automatic (configurable limits) |
| **Monitoring** | Basic logs | Cloud Logging + Monitoring |
| **Alerting** | None | Cloud Monitoring alerts |
| **Custom Domain** | Not available (Community) | Yes (Cloud Run custom domains) |
| **SSL/TLS** | Automatic | Automatic (managed certificates) |
| **Rollback** | Redeploy previous commit | Revision management |
| **Cost** | Free (Community tier) | Pay-per-use (~$0.33/month + storage) |
| **Maintenance** | Fully managed | Minimal (container updates) |
| **Uptime SLA** | Best-effort | 99.95% (with SLA) |

---

## Cost Comparison

### Streamlit Community Cloud

**Phase 1 (Free Tier):**
- ✅ **$0/month** for private apps
- ✅ Unlimited viewers (invited users)
- ⚠️ Limited compute resources
- ⚠️ No SLA guarantees

**Limitations:**
- 1 GB RAM per app
- Shared CPU
- No custom domain
- Community support only

### Google Cloud Run

**Phase 1 Estimate (Light Usage):**
- **Compute**: ~$0.10/month (minimal usage, auto-scales to zero)
- **Storage**: ~$0.20/month (Cloud Storage for 10 GB)
- **Networking**: ~$0.03/month (minimal egress)
- **Total**: ~$0.33/month (likely within free tier)

**Free Tier Includes:**
- 2 million requests/month
- 360,000 GB-seconds compute
- 180,000 vCPU-seconds
- 1 GB network egress/month
- 5 GB Cloud Storage

**Scaling Costs:**
- Scales with usage (requests, compute time, storage)
- Predictable pricing model
- Cost controls and budgets available

---

## Deployment Steps

### Streamlit Community Cloud (Phase 1)

**Prerequisites:**
- GitHub account with access to `jdanjohnson/Devpost-eoy-report-data`
- Streamlit Community Cloud account (free)

**Step 1: Prepare Repository**
```bash
# Commit hackathons_source.xlsx to the repository
git add data/hackathons_source.xlsx
git commit -m "Add hackathons source data for Streamlit Cloud deployment"
git push origin devin/1762825465-initial-deployment
```

**Step 2: Deploy to Streamlit Cloud**
1. Go to https://share.streamlit.io/
2. Click "New app"
3. Configure:
   - **Repository**: `jdanjohnson/Devpost-eoy-report-data`
   - **Branch**: `devin/1762825465-initial-deployment`
   - **Main file path**: `streamlit_app.py`
   - **App URL**: Choose a custom subdomain (e.g., `hackathon-analysis`)
4. Click "Deploy"
5. Wait 2-3 minutes for initial deployment

**Step 3: Configure Access**
1. Go to app settings → "Sharing"
2. Set app to **Private**
3. Add invited viewers by email (Streamlit accounts required)
4. Save settings

**Step 4: Verify Deployment**
1. Access the app URL (e.g., `https://hackathon-analysis.streamlit.app`)
2. Test all pages:
   - ✅ Upload page (upload sample Excel file)
   - ✅ Dashboard (view charts and data)
   - ✅ History (check job tracking)
   - ✅ Export (generate reports)
   - ✅ Hackathon Filter (test filtering by hackathon/organizer)
   - ✅ Timeline Analysis (verify time trends and charts)
3. Verify no errors in logs (Settings → Logs)

**Step 5: Share with Team**
- Share app URL with invited users
- Provide login instructions (Streamlit account required)
- Document data handling policy (ephemeral storage)

### Google Cloud Run (Phase 2+)

See `CLOUD_DEPLOYMENT.md` for detailed Google Cloud Run deployment instructions.

---

## Data Privacy & Compliance

### Streamlit Community Cloud

**Data Location:**
- Hosted on Streamlit Cloud infrastructure (AWS US-East)
- No data residency controls in Community tier

**Data Handling:**
- **User Uploads**: Processed in-memory and temporarily stored in container
- **Processed Data**: Stored in container filesystem (ephemeral)
- **Exports**: Generated on-demand and streamed to browser
- **Source Data**: Stored in private GitHub repository

**Privacy Considerations:**
- ✅ Private app (invite-only access)
- ✅ HTTPS/TLS encryption
- ✅ No data sharing with third parties
- ⚠️ Shared infrastructure (multi-tenant)
- ⚠️ Limited compliance certifications
- ⚠️ Data may persist in container until redeploy

**Recommendation for Maximum Privacy:**
- Implement "ephemeral mode" (process in `/tmp`, delete after use)
- Stream exports from memory (no disk writes)
- Provide "Purge All Data" button
- Add UI banner: "Data is not retained on server after processing"
- Avoid caching uploaded data in Streamlit session state

### Google Cloud Run

**Data Location:**
- Configurable region (e.g., `us-central1`, `europe-west1`)
- Data residency controls available

**Data Handling:**
- **User Uploads**: Stored in private Cloud Storage bucket
- **Processed Data**: Stored in Cloud Storage (durable)
- **Exports**: Stored in Cloud Storage output directory
- **Source Data**: Stored in Cloud Storage or container image

**Privacy Considerations:**
- ✅ Private Cloud Run service (no public access)
- ✅ IAM-controlled access
- ✅ Encryption at rest and in transit
- ✅ Cloud Audit Logs for access tracking
- ✅ VPC Service Controls for network isolation
- ✅ SOC 2, ISO 27001, HIPAA compliance available
- ✅ Data residency controls
- ✅ Customer-managed encryption keys (CMEK)

---

## Recommendation

### Phase 1: Streamlit Community Cloud ✅

**Use Streamlit Cloud if:**
- ✅ Single-user or small team access (< 10 users)
- ✅ Demo or proof-of-concept deployment
- ✅ Minimal operational overhead required
- ✅ Ephemeral storage is acceptable
- ✅ No strict compliance requirements
- ✅ Free tier is sufficient

**Implementation:**
1. Commit `hackathons_source.xlsx` to private GitHub repo
2. Deploy to Streamlit Cloud (one-click)
3. Set app to private and invite users
4. Document data handling policy
5. Test all features and verify no errors

### Phase 2+: Google Cloud Run

**Migrate to Cloud Run when:**
- Team-wide access required (> 10 users)
- Durable storage needed (persistent job history)
- Compliance requirements (SOC 2, HIPAA, etc.)
- Custom domain or branding required
- Advanced security controls needed (VPC, Cloud Armor)
- SLA guarantees required

---

## Frequently Asked Questions

### Q: Is my data safe on Streamlit Community Cloud?

**A:** Yes, with caveats:
- ✅ HTTPS/TLS encryption for all connections
- ✅ Private app (invite-only access)
- ✅ Secrets encrypted at rest
- ⚠️ Shared infrastructure (multi-tenant)
- ⚠️ Data may persist in container until redeploy
- ⚠️ No compliance certifications for Community tier

**Recommendation:** For maximum privacy, implement "ephemeral mode" to delete data immediately after processing.

### Q: What happens to my data when I redeploy?

**A:** On Streamlit Cloud:
- All files in the container filesystem are cleared
- Job history (SQLite) is lost
- Uploaded files and processed data are deleted
- Only code from GitHub remains

**Recommendation:** Export important data before redeploying, or migrate to Cloud Run for durable storage.

### Q: Can I use a custom domain?

**A:** 
- **Streamlit Cloud Community**: No custom domain support
- **Streamlit Cloud Teams/Enterprise**: Custom domain available
- **Google Cloud Run**: Custom domain supported (Cloud Run custom domains)

### Q: How do I handle large file uploads?

**A:**
- **Streamlit Cloud**: `maxUploadSize` set to 1024 MB (1 GB) in config
- **Google Cloud Run**: Configurable (up to 32 MB request body by default, use Cloud Storage for larger files)

**Recommendation:** For files > 1 GB, consider direct Cloud Storage upload with signed URLs.

### Q: Can I schedule automated processing?

**A:**
- **Streamlit Cloud**: No built-in scheduling (manual uploads only)
- **Google Cloud Run**: Use Cloud Scheduler to trigger processing jobs

### Q: How do I backup my data?

**A:**
- **Streamlit Cloud**: Export data manually before redeploys (no automatic backups)
- **Google Cloud Run**: Cloud Storage automatic backups, versioning, and lifecycle policies

---

## Next Steps

### For Phase 1 (Streamlit Cloud):

1. ✅ Commit `hackathons_source.xlsx` to repository
2. ✅ Update `.gitignore` to allow the file
3. ✅ Push changes to GitHub
4. ⏳ Deploy to Streamlit Community Cloud
5. ⏳ Configure private access and invite users
6. ⏳ Test all features and verify deployment
7. ⏳ Document data handling policy for team

### For Phase 2+ (Google Cloud Run):

See `CLOUD_DEPLOYMENT.md` for detailed migration instructions.

---

## Support & Resources

**Streamlit Community Cloud:**
- Documentation: https://docs.streamlit.io/streamlit-community-cloud
- Community Forum: https://discuss.streamlit.io/
- GitHub Issues: https://github.com/streamlit/streamlit/issues

**Google Cloud Run:**
- Documentation: https://cloud.google.com/run/docs
- Pricing Calculator: https://cloud.google.com/products/calculator
- Support: Google Cloud Support (paid tiers)

---

## Conclusion

For Phase 1, **Streamlit Community Cloud** provides the fastest path to deployment with minimal operational overhead. It is ideal for single-user demos and proof-of-concept deployments where ephemeral storage is acceptable.

For Phase 2+, **Google Cloud Run** offers durable storage, enterprise security controls, and compliance certifications at modest complexity and cost.

Both options are viable depending on your requirements, timeline, and operational constraints.
