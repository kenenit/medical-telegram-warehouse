with detections as (
    select * from {{ ref('stg_image_detections') }}
),

channels as (
    select * from {{ ref('dim_channels') }}
),

dates as (
    select * from {{ ref('dim_dates') }}
),

messages as (
    select * from {{ ref('fct_messages') }}
),

final as (
    select
        d.message_id::bigint,
        c.channel_key,
        dt.date_key,
        d.detected_class,
        d.confidence_score,
        d.image_category
    from detections d
    left join channels c
        on d.channel_name = c.channel_name
    left join messages m
        on d.message_id::bigint = m.message_id
    left join dates dt
        on m.date_key = dt.date_key
)

select * from final