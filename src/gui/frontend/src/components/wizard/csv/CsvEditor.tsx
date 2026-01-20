import { Tabs, Textarea, Button, Group, Stack, FileInput, Text, TextInput, Select, ActionIcon, Loader } from '@mantine/core'
import { IconUpload, IconPlus, IconMinus, IconRefresh, IconX } from '@tabler/icons-react'
import { useEffect, useState, useMemo } from 'react'
import { useWizard } from '../WizardContext'
import Spreadsheet from 'react-spreadsheet'
import Papa from 'papaparse'
import type { CellBase } from 'react-spreadsheet'
import { useUploadCsv, useCsvListQuery, useCsvContentQuery } from '../../../api/hooks'

export function CsvEditor() {
  const { state, setCSV } = useWizard()
  const [activeTab, setActiveTab] = useState<string | null>('spreadsheet')
  const [editorContent, setEditorContent] = useState(state.csv.content)
  const [filename, setFilename] = useState(state.csv.filename || 'wizard.csv')
  const [selectedFile, setSelectedFile] = useState('')
  const uploadCsv = useUploadCsv()
  const csvListQuery = useCsvListQuery()
  const csvContentQuery = useCsvContentQuery(selectedFile)

  // Sync wizard context CSV state to local editor state
  // Note: setFilename and setEditorContent are stable useState setters, not needed in deps
  useEffect(() => {
    if (state.csv.filename) {
      setFilename(state.csv.filename)
    }
    // Always sync content to ensure Text View updates when CSV is uploaded
    setEditorContent(state.csv.content)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.csv.filename, state.csv.content])

  // Sync selected file content to local state and wizard context
  useEffect(() => {
    if (csvContentQuery.data !== undefined && selectedFile) {
      setEditorContent(csvContentQuery.data)
      setFilename(selectedFile)
      setCSV(selectedFile, csvContentQuery.data)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [csvContentQuery.data, selectedFile])

  const handleTextChange = (value: string) => {
    const targetFilename = filename || 'wizard.csv'
    setEditorContent(value)
    setCSV(targetFilename, value)
  }

  const handleFileUpload = (file: File | null) => {
    if (!file) {
      // Clear button clicked - reset both spreadsheet and text views
      setEditorContent('')
      setFilename('wizard.csv')
      setCSV('wizard.csv', '')
      return
    }
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

  const handleRemoveRow = () => {
    const lines = editorContent.split('\n')
    if (lines.length <= 1) {
      // Don't remove if only header remains
      return
    }
    // Remove last row
    const newLines = lines.slice(0, -1)
    handleTextChange(newLines.join('\n'))
  }

  const handleSaveWorkspace = () => {
    const targetFilename = filename || 'wizard.csv'
    setCSV(targetFilename, editorContent)
    uploadCsv.mutate({ name: targetFilename, content: editorContent })
  }

  const handleClearSelection = () => {
    setSelectedFile('')
    setFilename('wizard.csv')
    setEditorContent('')
    setCSV('wizard.csv', '')
  }

  const handleRefresh = () => {
    csvListQuery.refetch()
    // Per CONTEXT.md: refresh ALWAYS clears selection
    handleClearSelection()
  }

  // Memoized options for CSV file selector
  const csvOptions = useMemo(
    () => (csvListQuery.data?.files ?? [])
      .sort((a, b) => a.localeCompare(b))
      .map((name) => ({ value: name, label: name })),
    [csvListQuery.data],
  )

  // Parse CSV to spreadsheet data
  const sheetData = useMemo(() => {
    if (activeTab !== 'spreadsheet') return []
    return parseCsvToSheet(editorContent)
  }, [editorContent, activeTab])

  const handleSheetChange = (data: Array<Array<CellBase | undefined>>) => {
    const headers = parseHeaders(editorContent)

    // Validation: Ensure column counts match to prevent data corruption
    if (data.length > 0 && data[0].length !== headers.length) {
      console.warn('Column count mismatch detected. Headers:', headers.length, 'Data columns:', data[0].length)
      // Attempt to normalize - pad or trim data to match header count
      const normalizedData = data.map(row => {
        const normalized = [...row]
        while (normalized.length < headers.length) {
          normalized.push({ value: '' })
        }
        return normalized.slice(0, headers.length)
      })
      const csv = sheetToCsv(normalizedData, headers)
      handleTextChange(csv)
      return
    }

    const csv = sheetToCsv(data, headers)
    handleTextChange(csv)
  }

  return (
    <Stack>
      {/* CSV File Selector */}
      {csvListQuery.isLoading ? (
        <Group gap="xs">
          <Loader size="sm" />
          <Text c="dimmed" size="sm">Loading CSV files...</Text>
        </Group>
      ) : (
        <Select
          label="Select CSV file"
          placeholder="Choose a file or type to search"
          searchable
          data={csvOptions}
          value={selectedFile || null}
          onChange={(value) => setSelectedFile(value || '')}
          nothingFoundMessage="No matching files"
          disabled={csvListQuery.isLoading}
          rightSection={
            <Group gap={4} wrap="nowrap">
              {selectedFile && (
                <ActionIcon
                  size="sm"
                  variant="subtle"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleClearSelection()
                  }}
                  aria-label="Clear selection"
                >
                  <IconX size={14} />
                </ActionIcon>
              )}
              <ActionIcon
                size="sm"
                variant="subtle"
                onClick={(e) => {
                  e.stopPropagation()
                  handleRefresh()
                }}
                loading={csvListQuery.isFetching}
                aria-label="Refresh file list"
              >
                <IconRefresh size={14} />
              </ActionIcon>
            </Group>
          }
          rightSectionPointerEvents="all"
          style={{ flex: 1, maxWidth: 400 }}
        />
      )}

      {csvContentQuery.isFetching && selectedFile && (
        <Text size="sm" c="dimmed">Loading file content...</Text>
      )}

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

      {/* Row 2: Add/Remove Row */}
      <Group>
        <Button leftSection={<IconPlus size={14} />} variant="light" onClick={handleAddRow}>
          Add Row
        </Button>
        <Button leftSection={<IconMinus size={14} />} variant="light" color="red" onClick={handleRemoveRow}>
          Remove Row
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
            styles={{ input: { fontFamily: 'monospace', fontSize: '0.85rem', minHeight: '400px' } }}
            minRows={25}
            maxRows={50}
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
  const result = Papa.parse(content, { header: false })
  const data = result.data as string[][]
  if (data.length === 0) return []
  return data[0].map(cell => cell ?? '')  // First row is headers
}

function sheetToCsv(data: Array<Array<CellBase | undefined>>, headers: string[]): string {
  const headerRow = headers.join(',')
  const rows = data.map((row) =>
    row.map((cell) => (cell?.value ?? '')).join(',')
  )
  return [headerRow, ...rows].join('\n')
}
