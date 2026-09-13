interface DetailFieldProps {
    label: string
    value: React.ReactNode
}

export function DetailField({
    label,
    value,
}: DetailFieldProps) {
    return (
        <div className="detail-field">
            <dt>{label}</dt>
            <dd>{value}</dd>
        </div>
    )
}