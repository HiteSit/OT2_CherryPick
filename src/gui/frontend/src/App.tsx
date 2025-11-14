import { AppShell, Container, Group, Tabs, Title } from '@mantine/core'
import { SettingsEditor } from './components/SettingsEditor'
import { WorkflowRunner } from './components/WorkflowRunner'
import { LabwareSummary } from './components/LabwareSummary'
import { CsvManager } from './components/CsvManager'
import './App.css'

function App() {
  return (
    <AppShell header={{ height: 60 }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" align="center" justify="space-between">
          <Title order={3}>OT-2 CherryPick Control</Title>
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Container size="lg" pb="xl">
          <Tabs defaultValue="settings" keepMounted>
            <Tabs.List>
              <Tabs.Tab value="settings">Settings</Tabs.Tab>
              <Tabs.Tab value="csvs">CSV Manager</Tabs.Tab>
              <Tabs.Tab value="workflow">Workflow</Tabs.Tab>
              <Tabs.Tab value="labware">Labware</Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="settings" pt="md">
              <SettingsEditor />
            </Tabs.Panel>

            <Tabs.Panel value="csvs" pt="md">
              <CsvManager />
            </Tabs.Panel>

            <Tabs.Panel value="workflow" pt="md">
              <WorkflowRunner />
            </Tabs.Panel>

            <Tabs.Panel value="labware" pt="md">
              <LabwareSummary />
            </Tabs.Panel>
          </Tabs>
        </Container>
      </AppShell.Main>
    </AppShell>
  )
}

export default App
