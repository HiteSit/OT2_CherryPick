import { Tabs, Textarea, Button, Group, Stack, FileInput, Text, TextInput } from '@mantine/core'
import { IconUpload, IconPlus, IconTablePlus } from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { useWizard } from '../WizardContext'
import Spreadsheet from 'react-spreadsheet'
import Papa from 'papaparse'
import type { CellBase } from 'react-spreadsheet'
import { useUploadCsv } from '../../../api/hooks'

export function CsvEditor() {
  const { state, setCSV } = useWizard()
  const [activeTab, setActiveTab] = useState<string | null>('spreadsheet')
  const [editorContent, setEditorContent] = useState(state.csv.content)
  const [filename, setFilename] = useState(state.csv.filename || 'wizard.csv')
  const uploadCsv = useUploadCsv()

  // Sync wizard context CSV state to local editor state
  // Note: setFilename and setEditorContent are stable useState setters, not needed in deps
  // The conditional prevents unnecessary updates when user is actively editing
  useEffect(() => {
    if (state.csv.filename) {
      setFilename(state.csv.filename)
    }
    if (state.csv.content !== editorContent) {
      setEditorContent(state.csv.content)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.csv.filename, state.csv.content])

  const handleTextChange = (value: string) => {
    const targetFilename = filename || 'wizard.csv'
    setEditorContent(value)
    setCSV(targetFilename, value)
  }

  const handleFileUpload = (file: File | null) => {
    if (!file) return
    const reader = new FileReader()
    reader.onload = (e) => {
      const content = e.target?.result as string
      setEditorContent(content)
      setFilename(file.name)
      setCSV(file.name, content)
      uploadCsv.mutate({ name: file.name, content })
    }
    reader.readAsText(file)
  }

  const handleAddRow = () => {
    const lines = editorContent.split('\n')
    const headers = lines[0] || 'Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well'
    const emptyRow = headers.split(',').map(() => '').join(',')
    const newContent = editorContent ? `${editorContent}\n${emptyRow}` : `${headers}\n${emptyRow}`
    handleTextChange(newContent)
  }

  const handleAddColumn = () => {
    const lines = editorContent.split('\n')
    if (lines.length === 0) {
      handleTextChange('New Column')
      return
    }
    const newLines = lines.map((line, idx) => {
      if (idx === 0) return `${line},New Column`
      return `${line},`
    })
    handleTextChange(newLines.join('\n'))
  }

  const handleSaveWorkspace = () => {
    const targetFilename = filename || 'wizard.csv'
    setCSV(targetFilename, editorContent)
    uploadCsv.mutate({ name: targetFilename, content: editorContent })
  }

  // Parse CSV to spreadsheet data
  const sheetData = activeTab === 'spreadsheet' ? parseCsvToSheet(editorContent) : []

  const handleSheetChange = (data: Array<Array<CellBase | undefined>>) => {
    const headers = parseHeaders(editorContent)
    const csv = sheetToCsv(data, headers)
    handleTextChange(csv)
  }

  return (
    <Stack>
      {/* Row 1: Filename and Upload */}
      <Group align="flex-end">
        <TextInput
          label="CSV filename"
          placeholder="wizard.csv"
          value={filename}
          onChange={(e) => {
            const next = e.target.value || 'wizard.csv'
            setFilename(next)
            setCSV(next, editorContent)
          }}
          style={{ flex: 1, maxWidth: 300 }}
        />
        <FileInput
          label="Upload CSV"
          placeholder="Choose file"
          leftSection={<IconUpload size={14} />}
          onChange={handleFileUpload}
          accept=".csv"
          clearable
          style={{ flex: 1, maxWidth: 300 }}
        />
      </Group>

      {/* Row 2: Add Row and Add Column */}
      <Group>
        <Button leftSection={<IconPlus size={14} />} variant="light" onClick={handleAddRow}>
          Add Row
        </Button>
        <Button leftSection={<IconTablePlus size={14} />} variant="light" onClick={handleAddColumn}>
          Add Column
        </Button>
      </Group>

      {/* Row 3: Save to workspace */}
      <Group>
        <Button variant="filled" onClick={handleSaveWorkspace} loading={uploadCsv.isPending}>
          Save to workspace
        </Button>
      </Group>

      {state.csv.filename && (
        <Text size="sm" c="dimmed">
          Current file: <strong>{state.csv.filename}</strong>
        </Text>
      )}

      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List>
          <Tabs.Tab value="spreadsheet">Spreadsheet View</Tabs.Tab>
          <Tabs.Tab value="text">Text View</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="spreadsheet" pt="md">
          <div style={{ overflow: 'auto', maxHeight: '500px' }}>
            <Spreadsheet
              data={sheetData}
              onChange={handleSheetChange}
              columnLabels={parseHeaders(editorContent)}
            />
          </div>
        </Tabs.Panel>

        <Tabs.Panel value="text" pt="md">
          <Textarea
            value={editorContent}
            onChange={(e) => handleTextChange(e.target.value)}
            styles={{ input: { fontFamily: 'monospace', fontSize: '0.85rem' } }}
            minRows={15}
            maxRows={25}
            placeholder="Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well"
          />
        </Tabs.Panel>
      </Tabs>
    </Stack>
  )
}

// Helper functions
function parseCsvToSheet(content: string): CellBase[][] {
  if (!content) return []
  const result = Papa.parse(content, { header: false })
  const data = result.data as string[][]

  // Skip header row for data
  return data.slice(1).map((row: string[]) =>
    row.map((cell: string) => ({ value: cell ?? '' }))
  )
}

function parseHeaders(content: string): string[] {
  if (!content) return []
  const lines = content.split('\n')
  if (lines.length === 0) return []
  return lines[0].split(',')
}

function sheetToCsv(data: Array<Array<CellBase | undefined>>, headers: string[]): string {
  const headerRow = headers.join(',')
  const rows = data.map((row) =>
    row.map((cell) => (cell?.value ?? '')).join(',')
  )
  return [headerRow, ...rows].join('\n')
}
