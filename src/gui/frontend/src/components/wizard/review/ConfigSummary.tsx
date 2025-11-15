import { Paper, Stack, Title, Text, Badge, Group, Grid } from '@mantine/core'
import { useWizard } from '../WizardContext'
import { useSettingsQuery } from '../../../api/hooks'

export function ConfigSummary() {
  const { state } = useWizard()
  const { data: settings } = useSettingsQuery()

  const general = settings?.settings?.general

  return (
    <Paper withBorder p="md">
      <Title order={4} mb="md">Configuration Summary</Title>

      <Grid>
        <Grid.Col span={6}>
          <Stack gap="xs">
            <div>
              <Text size="sm" fw={500}>Pipette Mode:</Text>
              <Badge color="blue" size="lg">
                {general?.mode || 'Not set'}
              </Badge>
            </div>

            <div>
              <Text size="sm" fw={500}>Tip Strategy:</Text>
              <Badge color="grape" size="lg">
                {general?.tip_reuse || 'Not set'}
              </Badge>
            </div>

            <div>
              <Text size="sm" fw={500}>Head Speed:</Text>
              <Text size="sm">{general?.head_speed?.speed || 400} mm/min</Text>
            </div>

            <div>
              <Text size="sm" fw={500}>Starting Tip Well:</Text>
              <Text size="sm">{general?.starting_tip_well || 'H1'}</Text>
            </div>
          </Stack>
        </Grid.Col>

        <Grid.Col span={6}>
          <Stack gap="xs">
            <div>
              <Text size="sm" fw={500}>Deck Layout:</Text>
              <Text size="sm">{state.deckLayout.length} labware configured</Text>
              <Text size="xs" c="dimmed">
                {state.deckLayout.filter(l => l.type === 'source').length} source |{' '}
                {state.deckLayout.filter(l => l.type === 'destination').length} destination |{' '}
                {state.deckLayout.filter(l => l.type === 'tip').length} tip racks
              </Text>
            </div>

            <div>
              <Text size="sm" fw={500}>Transfer Map:</Text>
              <Text size="sm">{state.csv.filename || 'No CSV loaded'}</Text>
              {state.csv.content && (
                <Text size="xs" c="dimmed">
                  {state.csv.content.split('\n').length - 1} rows
                </Text>
              )}
            </div>

            <div>
              <Text size="sm" fw={500}>Liquid Handling:</Text>
              <Group gap="xs">
                {settings?.settings?.liquid_handling?.pre_aspirate_contact?.enabled && (
                  <Badge size="xs" color="teal">Pre-Contact</Badge>
                )}
                {settings?.settings?.liquid_handling?.post_aspirate_wick?.enabled && (
                  <Badge size="xs" color="teal">Wick</Badge>
                )}
                {settings?.settings?.liquid_handling?.push_out?.enabled && (
                  <Badge size="xs" color="teal">Push-Out</Badge>
                )}
                {(settings?.settings?.liquid_handling?.delays?.post_aspirate ?? 0) > 0 && (
                  <Badge size="xs" color="orange">
                    Delay: {settings?.settings?.liquid_handling?.delays?.post_aspirate}s
                  </Badge>
                )}
              </Group>
            </div>
          </Stack>
        </Grid.Col>
      </Grid>
    </Paper>
  )
}
