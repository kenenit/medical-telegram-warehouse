with source as (
    select * from {{ ref('stg_telegram_messages') }}
),

final as (
    select
        row_number() over (order by channel_name)   as channel_key,
        channel_name,
        channel_title,
        case
            when lower(channel_name) like '%pharma%'
              or lower(channel_title) like '%pharma%'  then 'Pharmaceutical'
            when lower(channel_name) like '%cosmet%'
              or lower(channel_title) like '%cosmet%'  then 'Cosmetics'
            else 'Medical'
        end                                          as channel_type,
        min(message_date)                            as first_post_date,
        max(message_date)                            as last_post_date,
        count(*)                                     as total_posts,
        avg(views)                                   as avg_views
    from source
    group by channel_name, channel_title
)

select * from final
