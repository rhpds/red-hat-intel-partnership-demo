import { NavLink, Outlet } from 'react-router-dom';
import {
  Brand,
  Masthead,
  MastheadBrand,
  MastheadContent,
  MastheadMain,
  MastheadToggle,
  Nav,
  NavItem,
  NavList,
  Page,
  PageSidebar,
  PageSidebarBody,
  PageToggleButton,
  SkipToContent,
  Toolbar,
  ToolbarContent,
  ToolbarItem,
  Label,
  Divider,
} from '@patternfly/react-core';
import { BarsIcon } from '@patternfly/react-icons';
import { useHealth } from '../api/hooks';

const navItems = [
  { path: '/', label: 'Overview' },
  { path: '/architecture', label: 'Architecture' },
  { path: '/try-it', label: 'Try It' },
  { path: '/use-cases', label: 'Use Cases' },
  { path: '/operations', label: 'Operations' },
  { path: '/governance', label: 'Governance' },
  { path: '/overdrive', label: 'Overdrive' },
  { path: '/tokenizer', label: 'Tokenizer' },
  { path: '/docs', label: 'Documentation' },
];

export default function AppLayout() {
  const { data: health } = useHealth();

  const masthead = (
    <Masthead>
      <MastheadMain>
        <MastheadToggle>
          <PageToggleButton variant="plain" aria-label="Menu">
            <BarsIcon />
          </PageToggleButton>
        </MastheadToggle>
        <MastheadBrand>
          <Brand
            src="/intel-logo.svg"
            alt="Intel"
            heights={{ default: '28px' }}
          />
          <Divider orientation={{ default: 'vertical' }} style={{ margin: '0 10px' }} />
          <Brand
            src="/redhat-logo.svg"
            alt="Red Hat"
            heights={{ default: '28px' }}
          />
          <Divider orientation={{ default: 'vertical' }} style={{ margin: '0 10px' }} />
          <span style={{ fontSize: '0.95rem', fontWeight: 600, whiteSpace: 'nowrap' }}>
            Intel-Red Hat AI Inference Platform
          </span>
        </MastheadBrand>
      </MastheadMain>
      <MastheadContent>
        <Toolbar isStatic>
          <ToolbarContent>
            <ToolbarItem align={{ default: 'alignEnd' }}>
              <Label
                color={health?.status === 'healthy' ? 'green' : 'red'}
              >
                {health?.status === 'healthy' ? 'Platform Healthy' : 'Connecting...'}
              </Label>
            </ToolbarItem>
          </ToolbarContent>
        </Toolbar>
      </MastheadContent>
    </Masthead>
  );

  const sidebar = (
    <PageSidebar>
      <PageSidebarBody>
        <Nav aria-label="Main navigation">
          <NavList>
            {navItems.map(({ path, label }) => (
              <NavItem key={path}>
                <NavLink to={path} className={({ isActive }) => isActive ? 'pf-m-current' : ''}>
                  {label}
                </NavLink>
              </NavItem>
            ))}
          </NavList>
        </Nav>
      </PageSidebarBody>
    </PageSidebar>
  );

  return (
    <Page
      masthead={masthead}
      sidebar={sidebar}
      skipToContent={<SkipToContent href="#main-content">Skip to content</SkipToContent>}
    >
      <div id="main-content">
        <Outlet />
      </div>
    </Page>
  );
}
