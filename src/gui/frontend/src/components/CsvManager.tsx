import { useEffect, useMemo, useState } from 'react'
import {
  ActionIcon,
  Button,
  FileInput,
  Group,
  Loader,
  Paper,
  Select,
  Stack,
  Text,
  TextInput,
  Textarea,
  Title,
  Tooltip,
} from '@mantine/core'
import { IconDeviceFloppy, IconPlus, IconRefresh, IconTrash, IconUpload } from '@tabler/icons-react'
import Spreadsheet, { type Matrix } from 'react-spreadsheet'
import Papa from 'papaparse'
import { notifications } from '@mantine/notifications'
import { useCsvContentQuery, useCsvListQuery, useDeleteCsv, useUploadCsv } from '../api/hooks'

const defaultHeaders = ['Source Labware', 'Source Well', 'Volume (ul)', 'Dest Labware', 'Dest Well']

type Cell = { value: string }

type SheetData = Matrix<Cell>

const ensureHeaderRow = (sheet: SheetData): SheetData => {
  if (sheet.length === 0) {
    return [defaultHeaders.map((header) => ({ value: header }))]
  }
  return sheet
}

const parseCsvToSheet = (content: string): SheetData => {
  if (!content.trim()) {
    return ensureHeaderRow([])
  }
  const result = Papa.parse<string[]>(content, { header: false })
  const rows = result.data
    .filter((row) => row.length > 0)
    .map((row) => row.map((cell) => ({ value: cell ?? '' })))
  return ensureHeaderRow(rows)
}

const serializeSheetToCsv = (sheet: SheetData): string => {
  if (sheet.length === 0) {
    return ''
  }
  const headers = sheet[0].map((cell, idx) => cell?.value?.trim() || `Column ${idx + 1}`)
  const dataRows = sheet.slice(1).map((row) => headers.map((_, colIdx) => row[colIdx]?.value ?? ''))
  return Papa.unparse({ fields: headers, data: dataRows })
}

export function CsvManager() {
  const csvListQuery = useCsvListQuery()
  const [activeName, setActiveName] = useState('')
  const csvContentQuery = useCsvContentQuery(activeName)
  const uploadMutation = useUploadCsv()
  const deleteMutation = useDeleteCsv()
  const [editorContent, setEditorContent] = useState('')
  const [sheetData, setSheetData] = useState<SheetData>(ensureHeaderRow([]))
  const [gridDirty, setGridDirty] = useState(false)

  useEffect(() => {
    if (csvContentQuery.data !== undefined) {
      setEditorContent(csvContentQuery.data)
      setSheetData(parseCsvToSheet(csvContentQuery.data))
      setGridDirty(false)
    } else if (!activeName) {
      setEditorContent('')
      setSheetData(ensureHeaderRow([]))
      setGridDirty(false)
    }
  }, [csvContentQuery.data, activeName])

  const csvOptions = useMemo(
    () => (csvListQuery.data?.files ?? []).map((name) => ({ value: name, label: name })),
    [csvListQuery.data],
  )

  const handleFileUpload = async (file: File | null) => {
    if (!file) return
    const content = await file.text()
    uploadMutation.mutate(
      { name: file.name, content },
      {
        onSuccess: () => {
          setActiveName(file.name)
          notifications.show({ color: 'teal', title: 'CSV uploaded', message: `${file.name} saved.` })
        },
        onError: (error) =>
          notifications.show({ color: 'red', title: 'Upload failed', message: error instanceof Error ? error.message : 'Error' }),
      },
    )
  }

  const handleSave = () => {
    if (!activeName) {
      notifications.show({ color: 'red', title: 'Filename required', message: 'Enter a CSV name before saving.' })
      return
    }
    const contentToSave = gridDirty ? serializeSheetToCsv(sheetData) : editorContent
    uploadMutation.mutate(
      { name: activeName, content: contentToSave },
      {
        onSuccess: () => {
          notifications.show({ color: 'teal', title: 'CSV saved', message: `${activeName} updated.` })
          setEditorContent(contentToSave)
          setGridDirty(false)
        },
        onError: (error) =>
          notifications.show({ color: 'red', title: 'Save failed', message: error instanceof Error ? error.message : 'Error' }),
      },
    )
  }

  const handleDelete = () => {
    if (!activeName) return
    deleteMutation.mutate(activeName, {
      onSuccess: () => {
        notifications.show({ color: 'teal', title: 'Deleted', message: `${activeName} removed.` })
        setActiveName('')
        setEditorContent('')
        setSheetData(ensureHeaderRow([]))
        setGridDirty(false)
      },
      onError: (error) =>
        notifications.show({ color: 'red', title: 'Delete failed', message: error instanceof Error ? error.message : 'Error' }),
    })
  }

  const syncGridFromText = () => {
    setSheetData(parseCsvToSheet(editorContent))
    setGridDirty(false)
  }

  const syncTextFromGrid = () => {
    const serialized = serializeSheetToCsv(sheetData)
    setEditorContent(serialized)
    setGridDirty(false)
  }

  const addRow = () => {
    setSheetData((prev) => {
      const columnCount = prev[0]?.length ?? defaultHeaders.length
      const emptyRow = Array.from({ length: columnCount }, () => ({ value: '' }))
      return [...prev, emptyRow]
    })
    setGridDirty(true)
  }

  const addColumn = () => {
    setSheetData((prev) => {
      const columnCount = prev[0]?.length ?? defaultHeaders.length
      const newHeader = { value: `Column ${columnCount + 1}` }
      const next = prev.map((row, rowIndex) => {
        if (rowIndex === 0) {
          return [...row, newHeader]
        }
        return [...row, { value: '' }]
      })
      return next
    })
    setGridDirty(true)
  }

  const handleSheetChange = (data: SheetData) => {
    setSheetData(data)
    setGridDirty(true)
  }

  return (
    <Stack gap="lg">
      <Title order={4}>CSV Manager</Title>
      <Paper withBorder radius="md" p="md">
        <Stack gap="md">
          {csvListQuery.isLoading ? (
            <Group gap="xs">
              <Loader size="sm" />
              <Text c="dimmed">Loading available CSV files...</Text>
            </Group>
          ) : (
            <Select
              label="Existing CSV files"
              placeholder="Select a CSV to edit"
              searchable
              data={csvOptions}
              value={activeName}
              onChange={(value) => value && setActiveName(value)}
              nothingFoundMessage="No CSV files in workspace."
            />
          )}
          <FileInput
            label="Upload CSV file"
            placeholder="Drop or select a CSV"
            accept=".csv,text/csv"
            leftSection={<IconUpload size={16} />}
            onChange={handleFileUpload}
          />
        </Stack>
      </Paper>

      <Paper withBorder radius="md" p="md">
        <Stack gap="md">
          <TextInput
            label="Active filename"
            placeholder="example_basic.csv"
            value={activeName}
            onChange={(event) => setActiveName(event.currentTarget.value)}
          />
          {csvContentQuery.isFetching && activeName ? (
            <Group gap="xs">
              <Loader size="sm" />
              <Text c="dimmed">Loading CSV content...</Text>
            </Group>
          ) : (
            <Textarea
              label="CSV content"
              minRows={12}
              autosize
              value={editorContent}
              onChange={(event) => {
                setEditorContent(event.currentTarget.value)
                setGridDirty(false)
              }}
              styles={{ input: { fontFamily: 'monospace', fontSize: '0.85rem' } }}
              placeholder="Source Labware,Source Well,Volume (ul),..."
            />
          )}
          <Group gap="xs">
            <Button
              leftSection={<IconDeviceFloppy size={16} />}
              onClick={handleSave}
              loading={uploadMutation.isPending}
            >
              Save CSV
            </Button>
            <Button
              color="red"
              variant="light"
              leftSection={<IconTrash size={16} />}
              disabled={!activeName}
              loading={deleteMutation.isPending}
              onClick={handleDelete}
            >
              Delete
            </Button>
            <Tooltip label="Reload grid from text">
              <ActionIcon variant="default" onClick={syncGridFromText} aria-label="Sync grid from text">
                <IconRefresh size={16} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Rebuild CSV text from grid">
              <ActionIcon variant="default" onClick={syncTextFromGrid} aria-label="Sync text from grid">
                <IconDeviceFloppy size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Stack>
      </Paper>

      <Paper withBorder radius="md" p="md">
        <Group justify="space-between" mb="sm">
          <Text fw={500}>Spreadsheet view</Text>
          <Group gap="xs">
            <Button size="xs" leftSection={<IconPlus size={14} />} onClick={addRow}>
              Add row
            </Button>
            <Button size="xs" variant="default" leftSection={<IconPlus size={14} />} onClick={addColumn}>
              Add column
            </Button>
          </Group>
        </Group>
        <div style={{ overflow: 'auto' }}>
          <Spreadsheet data={sheetData} onChange={handleSheetChange} />
        </div>
      </Paper>
    </Stack>
  )
}
