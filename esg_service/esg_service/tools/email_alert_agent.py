"""
Email Alert Agent for sending covenant breach and portfolio summary notifications.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class EmailAlertAgent:
    """
    Agent for generating and sending email alerts for loan monitoring events.
    
    Capabilities:
    - Covenant breach notifications
    - Weekly portfolio summaries
    - ESG alert notifications
    - Risk committee briefings
    """
    
    def __init__(self):
        self.client = genai.Client()
        self.model_name = "gemini-2.0-flash-exp"
        
    async def generate_covenant_breach_email(
        self,
        loan_data: Dict[str, Any],
        breach_details: Dict[str, Any],
        recipients: List[str],
    ) -> Dict[str, Any]:
        """
        Generate and send covenant breach alert email.
        
        Args:
            loan_data: Loan information from BigQuery
            breach_details: Details of covenant breach
            recipients: List of email addresses
            
        Returns:
            Email send result with status and details
        """
        try:
            # Generate email content using Gemini
            prompt = f"""Generate a professional covenant breach alert email for a Risk Committee.

Loan Details:
- Loan ID: {loan_data.get('loan_id', 'N/A')}
- Borrower: {loan_data.get('borrower_name', 'N/A')}
- Facility Amount: ${loan_data.get('amount', 0):,.2f}
- Loan Officer: {loan_data.get('loan_officer', 'N/A')}

Breach Details:
- Covenant Type: {breach_details.get('covenant_type', 'N/A')}
- Threshold: {breach_details.get('threshold', 'N/A')}
- Actual Value: {breach_details.get('actual_value', 'N/A')}
- Breach Severity: {breach_details.get('severity', 'HIGH')}
- Detected: {breach_details.get('detected_date', 'N/A')}

Requirements:
1. Professional tone suitable for Risk Committee
2. Clear subject line with severity indicator
3. Concise executive summary
4. Detailed breach analysis
5. Recommended immediate actions
6. HTML format for professional appearance

Output as JSON with:
{{
    "subject": "Subject line",
    "html_body": "Full HTML email body",
    "plain_text": "Plain text version"
}}"""

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            
            # Parse email content
            import json
            email_content = json.loads(response.text.strip())
            
            # Send email using notification tools
            from alert_service.alert_service.tools.notification_tools import send_email
            
            result = send_email(
                to_emails=recipients,
                subject=email_content['subject'],
                body=email_content['plain_text'],
                html_body=email_content['html_body'],
            )
            
            logger.info(f"Covenant breach email sent for loan {loan_data.get('loan_id')}")
            
            return {
                'success': result.get('success', False),
                'loan_id': loan_data.get('loan_id'),
                'recipients': recipients,
                'subject': email_content['subject'],
                'send_result': result,
            }
            
        except Exception as e:
            logger.error(f"Failed to generate/send covenant breach email: {e}")
            return {
                'success': False,
                'error': str(e),
                'loan_id': loan_data.get('loan_id'),
            }
    
    async def generate_portfolio_summary_email(
        self,
        portfolio_data: Dict[str, Any],
        recipients: List[str],
        period: str = "weekly",
    ) -> Dict[str, Any]:
        """
        Generate and send portfolio summary email.
        
        Args:
            portfolio_data: Portfolio metrics from BigQuery
            recipients: List of email addresses
            period: Reporting period (weekly, monthly)
            
        Returns:
            Email send result
        """
        try:
            # Extract key metrics
            total_loans = portfolio_data.get('total_loans', 0)
            total_exposure = portfolio_data.get('total_exposure', 0)
            high_risk_loans = portfolio_data.get('high_risk_count', 0)
            covenant_breaches = portfolio_data.get('covenant_breaches', 0)
            avg_esg_score = portfolio_data.get('avg_esg_score', 0)
            
            prompt = f"""Generate a professional {period} portfolio summary email for senior management.

Portfolio Metrics:
- Total Active Loans: {total_loans}
- Total Exposure: ${total_exposure:,.2f}
- High-Risk Loans: {high_risk_loans} ({high_risk_loans/total_loans*100 if total_loans > 0 else 0:.1f}%)
- Covenant Breaches: {covenant_breaches}
- Average ESG Score: {avg_esg_score:.2f}/100
- Greener Lending %: {portfolio_data.get('green_loan_percentage', 0):.1f}%

Top Concerns:
{', '.join(portfolio_data.get('top_concerns', ['No major concerns']))}

Requirements:
1. Executive summary with key highlights
2. Risk assessment summary
3. ESG performance overview
4. Action items and recommendations
5. Professional HTML format with charts described textually

Output as JSON with:
{{
    "subject": "Subject line",
    "html_body": "Full HTML email body",
    "plain_text": "Plain text version"
}}"""

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            
            # Parse and send
            import json
            email_content = json.loads(response.text.strip())
            
            from alert_service.alert_service.tools.notification_tools import send_email
            
            result = send_email(
                to_emails=recipients,
                subject=email_content['subject'],
                body=email_content['plain_text'],
                html_body=email_content['html_body'],
            )
            
            logger.info(f"{period.capitalize()} portfolio summary sent to {len(recipients)} recipients")
            
            return {
                'success': result.get('success', False),
                'period': period,
                'recipients': recipients,
                'subject': email_content['subject'],
                'send_result': result,
            }
            
        except Exception as e:
            logger.error(f"Failed to generate/send portfolio summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'period': period,
            }
    
    async def generate_esg_alert_email(
        self,
        alert_data: Dict[str, Any],
        recipients: List[str],
    ) -> Dict[str, Any]:
        """
        Generate and send ESG-related alert email.
        
        Args:
            alert_data: ESG alert details
            recipients: Email recipients
            
        Returns:
            Send result
        """
        try:
            alert_type = alert_data.get('alert_type', 'ESG_ALERT')
            borrower = alert_data.get('borrower_name', 'Unknown')
            issue = alert_data.get('issue_description', 'N/A')
            
            prompt = f"""Generate professional ESG alert email.

Alert Type: {alert_type}
Borrower: {borrower}
Issue: {issue}
Severity: {alert_data.get('severity', 'MEDIUM')}
Data Source: {alert_data.get('data_source', 'Internal monitoring')}

Generate concise, actionable email.

Output as JSON:
{{
    "subject": "Subject",
    "html_body": "HTML body",
    "plain_text": "Plain text"
}}"""

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            
            import json
            email_content = json.loads(response.text.strip())
            
            from alert_service.alert_service.tools.notification_tools import send_email
            
            result = send_email(
                to_emails=recipients,
                subject=email_content['subject'],
                body=email_content['plain_text'],
                html_body=email_content['html_body'],
            )
            
            return {
                'success': result.get('success', False),
                'alert_type': alert_type,
                'recipients': recipients,
                'send_result': result,
            }
            
        except Exception as e:
            logger.error(f"Failed to send ESG alert: {e}")
            return {
                'success': False,
                'error': str(e),
            }


# Synchronous wrapper functions for tool registration
def send_covenant_breach_alert(
    loan_id: str,
    breach_type: str,
    threshold: str,
    actual_value: str,
    severity: str = "HIGH",
) -> Dict[str, Any]:
    """
    Send covenant breach alert email.
    
    Args:
        loan_id: Loan identifier
        breach_type: Type of covenant breached
        threshold: Covenant threshold
        actual_value: Actual value that breached
        severity: Breach severity (HIGH, MEDIUM, LOW)
        
    Returns:
        Send result
    """
    import asyncio
    from common.bigquery_client import get_bigquery_client
    # Get loan data from BigQuery
    bq_client = get_bigquery_client()
    query = f"""
    SELECT 
        loan_id,
        borrower_name,
        amount,
        loan_officer,
        currency
    FROM `{bq_client.project_id}.{bq_client.dataset_id}.loans`
    WHERE loan_id = '{loan_id}'
    LIMIT 1
    """
    
    try:
        results = bq_client.execute_query(query)
        if not results:
            return {'success': False, 'error': 'Loan not found'}
        
        loan_data = dict(results[0])
        
        breach_details = {
            'covenant_type': breach_type,
            'threshold': threshold,
            'actual_value': actual_value,
            'severity': severity,
            'detected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # Get recipients based on severity from database
        from alert_service.alert_service.tools.notification_tools import get_notification_recipients
        
        recipients_data = get_notification_recipients(loan_id, severity)
        recipients = recipients_data.get('email_recipients', [])
        
        # Fail if no recipients configured (no hardcoded fallback)
        if not recipients:
            logger.error(f"No recipients configured for {severity} severity")
            return {
                'success': False,
                'error': f'No recipients configured for severity {severity}',
                'loan_id': loan_id,
                'severity': severity
            }
        
        # Send email
        agent = EmailAlertAgent()
        result = asyncio.run(agent.generate_covenant_breach_email(
            loan_data, breach_details, recipients
        ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending covenant breach alert: {e}")
        return {'success': False, 'error': str(e)}


def send_portfolio_summary(
    period: str = "weekly",
    recipients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send portfolio summary email.
    
    Args:
        period: Reporting period (weekly, monthly)
        recipients: Email recipients (defaults to management team)
        
    Returns:
        Send result
    """
    import asyncio
    from common.bigquery_client import get_bigquery_client
    
    # Fetch default recipients from BigQuery notification_config table
    if recipients is None:
        bq_client = get_bigquery_client()
        query = f"""
        SELECT email
        FROM `{bq_client.project_id}.{bq_client.dataset_id}.notification_config`
        WHERE severity = 'PORTFOLIO'
          AND active = true
        ORDER BY role
        """
        
        try:
            results = bq_client.execute_query(query)
            recipients = [row['email'] for row in results] if results else []
            
            if not recipients:
                logger.error("No portfolio summary recipients configured in database")
                return {
                    'success': False,
                    'error': 'No recipients configured for portfolio summaries. Please add recipients to notification_config table with severity=PORTFOLIO'
                }
        except Exception as e:
            logger.error(f"Failed to fetch portfolio recipients from database: {e}")
            return {'success': False, 'error': f'Database error: {str(e)}'}
    
    # Get portfolio metrics from BigQuery
    bq_client = get_bigquery_client()
    query = f"""
    SELECT 
        COUNT(DISTINCT loan_id) as total_loans,
        SUM(amount) as total_exposure,
        SUM(CASE WHEN ml_breach_probability > 0.7 THEN 1 ELSE 0 END) as high_risk_count,
        SUM(CASE WHEN covenant_status = 'BREACH' THEN 1 ELSE 0 END) as covenant_breaches,
        AVG(esg_composite_score) as avg_esg_score,
        SUM(CASE WHEN tlp_category IN ('GREEN', 'SOCIAL') THEN amount ELSE 0 END) / SUM(amount) * 100 as green_loan_percentage
    FROM `{bq_client.project_id}.{bq_client.dataset_id}.loans`
    WHERE loan_status = 'ACTIVE'
    """
    
    try:
        results = bq_client.execute_query(query)
        if not results:
            return {'success': False, 'error': 'No portfolio data'}
        
        portfolio_data = dict(results[0])
        portfolio_data['top_concerns'] = ['High breach probability loans require review']
        
        agent = EmailAlertAgent()
        result = asyncio.run(agent.generate_portfolio_summary_email(
            portfolio_data, recipients, period
        ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending portfolio summary: {e}")
        return {'success': False, 'error': str(e)}
