import { Grid, Paper, Title, Stack } from '@mantine/core'
import { CsvEditor } from '../csv/CsvEditor'
import { TransferPreview } from '../csv/TransferPreview'
import { ValidationPanel } from '../csv/ValidationPanel'
import { useWizard } from '../WizardContext'

export function TransferMapStep() {
  const { state } = useWizard()

  return (
    <Stack>
      {/* Row 1: CSV Editor + Validation Panel */}
      <Grid>
        <Grid.Col span={9}>
          <Paper withBorder p="md">
            <Title order={4} mb="md">CSV Transfer Map</Title>
            <CsvEditor />
          </Paper>
        </Grid.Col>
        <Grid.Col span={3}>
          <Paper withBorder p="md" style={{ position: 'sticky', top: 20 }}>
            <ValidationPanel
              csvContent={state.csv.content}
              deckLayout={state.deckLayout}
            />
          </Paper>
        </Grid.Col>
      </Grid>

      {/* Row 2: Transfer Preview (full width below) */}
      <Paper withBorder p="md">
        <TransferPreview csvContent={state.csv.content} />
      </Paper>
    </Stack>
  )
}
