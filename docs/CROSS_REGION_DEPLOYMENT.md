# Cross-Region Deployment Guide

## Deploy in EU, Call Bedrock in US

Yes! You can deploy your application in **eu-west-1** (or any region) and call Amazon Bedrock Nova Canvas in **us-east-1**.

## Why Do This?

1. **Lower latency for EU users** - App runs closer to your users
2. **Data residency** - Keep user data in EU
3. **Service availability** - Use Bedrock even if not available in your region
4. **Cost optimization** - Deploy where compute is cheaper

## How It Works

The application uses **two separate regions**:

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  User in Europe                                          │
│       ↓                                                  │
│  ECS App in eu-west-1 (Low latency)                     │
│       ↓                                                  │
│  Bedrock API in us-east-1 (Cross-region call)          │
│       ↓                                                  │
│  Generated badge returned to user                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Configuration

Two environment variables control the regions:

1. **AWS_REGION** - Where your ECS app runs (eu-west-1)
2. **BEDROCK_REGION** - Where Bedrock API calls go (us-east-1)

## Deployment Options

### Option 1: Deploy in EU, Bedrock in US (Recommended for EU users)

```bash
AWS_REGION=eu-west-1 BEDROCK_REGION=us-east-1 ./deploy-to-ecs-express.sh
```

**Result:**
- App URL: `https://digital-badge-app.ecs.eu-west-1.on.aws`
- Bedrock calls: us-east-1
- User latency: Low (EU)
- Bedrock latency: ~100ms cross-region

### Option 2: Deploy in US West, Bedrock in US East

```bash
AWS_REGION=us-west-2 BEDROCK_REGION=us-east-1 ./deploy-to-ecs-express.sh
```

**Result:**
- App URL: `https://digital-badge-app.ecs.us-west-2.on.aws`
- Bedrock calls: us-east-1
- User latency: Low (US West)
- Bedrock latency: ~50ms cross-region

### Option 3: Everything in Same Region (Lowest Bedrock latency)

```bash
AWS_REGION=us-east-1 ./deploy-to-ecs-express.sh
```

**Result:**
- App URL: `https://digital-badge-app.ecs.us-east-1.on.aws`
- Bedrock calls: us-east-1 (same region)
- User latency: Depends on user location
- Bedrock latency: Minimal (~10ms)

## Performance Considerations

### Latency Breakdown

**EU User → EU App → US Bedrock:**
```
User → App:        ~20ms  (EU to EU)
App → Bedrock:     ~100ms (EU to US)
Bedrock Processing: ~3-5s  (Image generation)
Total:             ~3.1-5.1s
```

**EU User → US App → US Bedrock:**
```
User → App:        ~100ms (EU to US)
App → Bedrock:     ~10ms  (US to US)
Bedrock Processing: ~3-5s  (Image generation)
Total:             ~3.1-5.1s
```

**Verdict:** Cross-region Bedrock calls add ~100ms, which is negligible compared to the 3-5 second image generation time.

### Recommendations by User Location

| User Location | Deploy Region | Bedrock Region | Rationale |
|---------------|---------------|----------------|-----------|
| Europe | eu-west-1 | us-east-1 | Low user latency, acceptable Bedrock latency |
| US East | us-east-1 | us-east-1 | Lowest overall latency |
| US West | us-west-2 | us-east-1 | Low user latency, acceptable Bedrock latency |
| Asia | ap-southeast-1 | us-east-1 | Low user latency, higher Bedrock latency |
| Global | us-east-1 | us-east-1 | Central location, use CloudFront CDN |

## IAM Permissions

Your ECS task role needs Bedrock permissions in the **Bedrock region**:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["bedrock:InvokeModel"],
    "Resource": ["arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-canvas-v1:0"]
  }]
}
```

The deployment script creates this automatically with the correct region.

## Cost Implications

### Data Transfer Costs

**Cross-region data transfer:**
- Out from eu-west-1 to us-east-1: $0.02/GB
- In to eu-west-1 from us-east-1: Free

**Typical badge generation:**
- Request to Bedrock: ~1KB (negligible)
- Response from Bedrock: ~500KB (image)
- Cost per badge: ~$0.00001 (1/100th of a cent)

**For 10,000 badges/month:**
- Data transfer: ~5GB
- Cost: ~$0.10/month

**Verdict:** Cross-region data transfer cost is negligible.

### Bedrock API Costs

Bedrock pricing is the **same in all regions**:
- Nova Canvas: $0.040 per image (1024x1024)

No cost difference for cross-region calls.

## Example Deployments

### Example 1: EU Deployment

```bash
# Set regions
export AWS_REGION=eu-west-1
export BEDROCK_REGION=us-east-1

# Deploy
./deploy-to-ecs-express.sh
```

**Configuration:**
- ECS Service: eu-west-1
- ECR Repository: eu-west-1
- ALB: eu-west-1
- Bedrock API: us-east-1

**Environment Variables in Container:**
```bash
AWS_REGION=eu-west-1
BEDROCK_REGION=us-east-1
BASE_URL=https://digital-badge-app.ecs.eu-west-1.on.aws
```

### Example 2: Asia Deployment

```bash
export AWS_REGION=ap-southeast-1
export BEDROCK_REGION=us-east-1
./deploy-to-ecs-express.sh
```

### Example 3: Same Region (Simplest)

```bash
export AWS_REGION=us-east-1
# BEDROCK_REGION defaults to AWS_REGION
./deploy-to-ecs-express.sh
```

## Testing Cross-Region Setup

### Test Locally

```bash
# Set both regions
export AWS_REGION=eu-west-1
export BEDROCK_REGION=us-east-1

# Run the app
uv run python run.py
```

### Test with Finch

```bash
finch run -p 8080:8080 \
    -e AWS_REGION=eu-west-1 \
    -e BEDROCK_REGION=us-east-1 \
    -e SECRET_KEY=test \
    digital-badge-app
```

### Verify Bedrock Region

Check the logs to see which region Bedrock is using:

```bash
# After deployment
aws logs tail /aws/ecs/express/digital-badge-app --follow

# Look for Bedrock API calls
# Should show: "Calling Bedrock in region: us-east-1"
```

## Troubleshooting

### Error: "Could not connect to Bedrock"

**Cause:** IAM role doesn't have permissions in the Bedrock region

**Solution:**
```bash
# Check IAM role has Bedrock permissions
aws iam get-role-policy --role-name badgeAppTaskRole --policy-name BedrockAccess

# Should show us-east-1 in the resource ARN
```

### Error: "Model not found"

**Cause:** Nova Canvas not enabled in the Bedrock region

**Solution:**
```bash
# Enable model access in us-east-1
aws bedrock list-foundation-models --region us-east-1 | grep nova-canvas

# If not available, enable in Bedrock console
```

### High Latency

**Symptom:** Badge generation takes >10 seconds

**Diagnosis:**
- Check CloudWatch logs for timing
- Most time is image generation (3-5s), not network

**Solution:**
- Cross-region latency is normal (~100ms)
- Consider caching generated badges
- Use async badge generation for better UX

## Monitoring

### CloudWatch Metrics

Monitor cross-region performance:

```bash
# View Bedrock API latency
aws cloudwatch get-metric-statistics \
    --namespace AWS/Bedrock \
    --metric-name InvocationLatency \
    --dimensions Name=ModelId,Value=amazon.nova-canvas-v1:0 \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-02T00:00:00Z \
    --period 3600 \
    --statistics Average \
    --region us-east-1
```

### Application Logs

Add timing logs to track cross-region calls:

```python
import time
start = time.time()
# Bedrock API call
duration = time.time() - start
print(f"Bedrock call took {duration:.2f}s")
```

## Best Practices

### 1. Use Same Region When Possible
If Bedrock is available in your deployment region, use it:
```bash
# Both in us-east-1
AWS_REGION=us-east-1 ./deploy-to-ecs-express.sh
```

### 2. Cache Generated Images
Store generated badges in S3 to avoid repeated Bedrock calls:
```python
# Check S3 cache first
# Only call Bedrock if not cached
```

### 3. Async Badge Generation
Generate badges asynchronously to improve UX:
```python
# Return immediately with "processing" status
# Generate badge in background
# Notify user when ready
```

### 4. Monitor Costs
Track cross-region data transfer:
```bash
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --filter file://filter.json
```

## Summary

**Yes, you can deploy in eu-west-1 and call Bedrock in us-east-1!**

**To deploy:**
```bash
AWS_REGION=eu-west-1 BEDROCK_REGION=us-east-1 ./deploy-to-ecs-express.sh
```

**Trade-offs:**
- ✅ Lower latency for EU users
- ✅ Data residency compliance
- ✅ Negligible cost increase (~$0.10/month for 10k badges)
- ⚠️ ~100ms additional latency for Bedrock calls (minimal impact)

**Recommended for:**
- EU-based users
- Data residency requirements
- When Bedrock not available in your region

The cross-region latency is negligible compared to the 3-5 second image generation time!
