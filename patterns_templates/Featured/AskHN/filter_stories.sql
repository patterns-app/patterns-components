select * from {{ Table("hn_items") }}
where
    type = 'story' and
    dead = 'FALSE' and
    descendants > 3 and
    score > 20