import { AppShell, Group, Title } from '@mantine/core'
import { ProtocolWizard } from './components/wizard/ProtocolWizard'
import './App.css'

function App() {
  return (
    <AppShell header={{ height: 60 }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" align="center" justify="space-between">
          <Title order={3}>OT-2 CherryPick Protocol Generator</Title>
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <ProtocolWizard />
      </AppShell.Main>
    </AppShell>
  )
}

export default App
