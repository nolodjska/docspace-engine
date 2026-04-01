import { renderSidebar } from '../src/sidebar.js'

test('renders sidebar', () => {
  expect(renderSidebar()).toBe('sidebar')
})
