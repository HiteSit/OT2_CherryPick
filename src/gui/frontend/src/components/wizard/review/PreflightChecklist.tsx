import { Paper, Title, List, ThemeIcon, Text } from '@mantine/core'
import { IconCheck, IconAlertTriangle, IconX } from '@tabler/icons-react'
import { useWizard } from '../WizardContext'
import { useSettingsQuery } from '../../../api/hooks'

export function PreflightChecklist() {
  const { state } = useWizard()
  const { data: settings } = useSettingsQuery()

  const checks = [
    {
      condition: state.deckLayout.some(l => l.type === 'source'),
      message: 'Deck has source labware',
      severity: 'error' as const
    },
    {
      condition: state.deckLayout.some(l => l.type === 'destination'),
      message: 'Deck has destination labware',
      severity: 'error' as const
    },
    {
      condition: state.deckLayout.some(l => l.type === 'tip'),
      message: 'Deck has tip racks',
      severity: 'error' as const
    },
    {
      condition: settings !== null && settings !== undefined,
      message: 'Settings configured',
      severity: 'error' as const
    },
    {
      condition: state.csv.content.length > 0,
      message: 'CSV transfer map loaded',
      severity: 'error' as const
    },
    {
      condition: state.csv.filename !== '',
      message: 'CSV has valid filename',
      severity: 'warning' as const
    },
    {
      // Check for duplicate deck slots
      condition: (() => {
        const slots = state.deckLayout
          .map(l => l.position_rack)
          .filter(s => s !== undefined)
        return new Set(slots).size === slots.length
      })(),
      message: 'No duplicate deck slots',
      severity: 'error' as const
    },
    {
      condition: state.deckLayout.length <= 11,
      message: 'Deck slot count within limits (max 11)',
      severity: 'error' as const
    }
  ]

  const hasErrors = checks.some(c => c.severity === 'error' && !c.condition)
  const hasWarnings = checks.some(c => c.severity === 'warning' && !c.condition)

  return (
    <Paper withBorder p="md">
      <Title order={4} mb="md">Pre-flight Checklist</Title>

      {hasErrors && (
        <Text size="sm" c="red" mb="md" fw={500}>
          ❌ Fix errors before running workflow
        </Text>
      )}

      {!hasErrors && hasWarnings && (
        <Text size="sm" c="orange" mb="md" fw={500}>
          ⚠️ Warnings present - review before proceeding
        </Text>
      )}

      {!hasErrors && !hasWarnings && (
        <Text size="sm" c="green" mb="md" fw={500}>
          ✅ All checks passed - ready to execute
        </Text>
      )}

      <List spacing="xs">
        {checks.map((check, i) => (
          <List.Item
            key={i}
            icon={
              <ThemeIcon
                color={check.condition ? 'green' : (check.severity === 'error' ? 'red' : 'orange')}
                size={20}
                radius="xl"
              >
                {check.condition ? (
                  <IconCheck size={12} />
                ) : check.severity === 'error' ? (
                  <IconX size={12} />
                ) : (
                  <IconAlertTriangle size={12} />
                )}
              </ThemeIcon>
            }
          >
            <Text size="sm">{check.message}</Text>
          </List.Item>
        ))}
      </List>
    </Paper>
  )
}
