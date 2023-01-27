SELECT investor_name, SUM(raised_amount_usd) AS total_investments
FROM {{ Table("investments")}} investments
INNER JOIN {{ Table("funding_rounds")}} funding_rounds
ON investments.funding_round_uuid = funding_rounds.uuid
INNER JOIN {{ Table("organizations")}} organizations
ON funding_rounds.org_uuid = organizations.uuid
WHERE investor_type = 'organization'
    AND EXTRACT(year FROM announced_on) = 2022
    AND category_list iLIKE '%biotech%'
GROUP BY investor_name
ORDER BY total_investments DESC nulls last;