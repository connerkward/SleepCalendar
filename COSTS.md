# Cloud Run Cost Estimate

## Free Tier (Monthly)

Google Cloud Run provides significant free tier allowances:

- **180,000 vCPU-seconds** (2 vCPU running for 25 hours/month)
- **360,000 GiB-seconds memory** (512 MB running for ~200 hours/month)
- **2 million requests**
- **1 GB outbound networking** (North America)

## Estimated Monthly Costs

### Light Usage (Few Users)
- **Requests**: ~1,000/month
- **Compute**: ~256 MB, 0.5 vCPU, ~500ms per request
- **Cost**: **$0/month** (fully covered by free tier)

### Moderate Usage (1,000 Users)
- **Requests**: ~2.88 million/month (1000 users × 1 sync/day × 30 days)
- **Compute**: ~512 MB, 1 vCPU, ~1s per request
- **Cost**: **$5-20/month**
  - Most requests covered by free tier
  - Small charges for excess compute/memory

### High Usage (10,000+ Users)
- **Requests**: ~30 million/month
- **Compute**: ~512 MB, 1 vCPU, ~1s per request
- **Cost**: **$50-200/month**
  - Significant compute beyond free tier
  - Higher request volumes

## Google Calendar API Costs

**Free** - No cost for Calendar API usage within quotas:
- Per-project quota: 1 million queries/day
- Per-user quota: Varies by operation type
- No charges, only rate limiting when exceeded

## Rate Limiting Protection

The API implements rate limiting to protect against abuse:
- **30 requests per minute** per IP address
- **500 requests per hour** per IP address
- Prevents cost spikes from malicious/bot traffic

## Cost Optimization Tips

1. **Use minimum instances**: Set `min-instances=0` (scale to zero)
2. **Optimize memory**: Use 512 MB (sufficient for most requests)
3. **Set max instances**: Limit to 10 to cap concurrent requests
4. **Monitor usage**: Set up Cloud Monitoring alerts for cost thresholds
5. **Use Cloud Run's free tier**: Deploy in us-central1 for best free tier coverage

## Monthly Cost Monitoring

To monitor costs:

```bash
# View current month costs
gcloud billing accounts list
gcloud billing projects describe PROJECT_ID

# Set up budget alerts in Cloud Console
# Console > Billing > Budgets & alerts
```

## Expected Cost for This Project

For typical sleep data sync usage (1-2 requests per user per day):
- **Small scale (100-500 users)**: $0-5/month
- **Medium scale (1,000-5,000 users)**: $10-50/month
- **Large scale (10,000+ users)**: $50-200/month

Most deployments will stay within free tier for months, especially with rate limiting protection.
