with messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

channels as (
    select * from {{ ref('dim_channels') }}
),

dates as (
    select * from {{ ref('dim_dates') }}
),

final as (
    select
        m.message_id,
        c.channel_key,
        d.date_key,
        m.message_text,
        m.message_length,
        m.views,
        m.forwards,
        m.has_image
    from messages m
    left join channels c
        on m.channel_name = c.channel_name
    left join dates d
        on d.full_date = m.message_date::date
)

select * from final