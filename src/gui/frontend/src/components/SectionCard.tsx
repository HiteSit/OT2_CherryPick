import { Card, Stack, Title } from '@mantine/core'
import type { CardProps } from '@mantine/core'
import type { PropsWithChildren, ReactNode } from 'react'

interface SectionCardProps extends CardProps {
  title: ReactNode
  description?: ReactNode
}

export function SectionCard({ title, description, children, ...rest }: PropsWithChildren<SectionCardProps>) {
  return (
    <Card withBorder radius="md" shadow="sm" {...rest}>
      <Stack gap="xs">
        <div>
          <Title order={4}>{title}</Title>
          {description}
        </div>
        {children}
      </Stack>
    </Card>
  )
}
