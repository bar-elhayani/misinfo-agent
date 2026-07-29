with metrics as (
    select * from {{ ref('int_network_metrics') }}
),

classified as (
    select
        *,
        case
            when num_nodes <= 20 then 'small'
            when num_nodes <= 100 then 'medium'
            else 'large'
        end as spread_size_bucket,

        case
            when avg_out_degree >= 20 then true
            else false
        end as high_amplification_flag

    from metrics
)

select
    graph_id,
    source_dataset,
    split,
    label,
    num_nodes,
    edge_count,
    unique_source_nodes,
    unique_target_nodes,
    avg_out_degree,
    has_no_spread,
    spread_size_bucket,
    high_amplification_flag

from classified
