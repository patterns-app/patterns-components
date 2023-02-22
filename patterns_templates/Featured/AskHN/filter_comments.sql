select * from {{ Table("hn_items") }}
where
    type = 'comment' and
    dead = 'FALSE' and
    length(post_text) > 200 and
    id > 20000000
;
