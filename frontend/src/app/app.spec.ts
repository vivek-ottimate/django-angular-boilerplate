import { TestBed } from '@angular/core/testing';
import { NEVER, of, throwError } from 'rxjs';
import { App } from './app';
import { ApiService } from './api.service';

describe('App', () => {
  const mockApiService = { getHello: vi.fn() };

  beforeEach(async () => {
    mockApiService.getHello.mockReset();
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [{ provide: ApiService, useValue: mockApiService }],
    }).compileComponents();
  });

  async function render() {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    return { fixture, el: fixture.nativeElement as HTMLElement };
  }

  it('should create the app', async () => {
    const { fixture } = await render();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should show nothing before ping button is clicked', async () => {
    const { el } = await render();
    expect(el.querySelector('.message')).toBeNull();
    expect(el.querySelector('.count')).toBeNull();
    expect(el.querySelector('.error')).toBeNull();
  });

  it('should display message and ping count on success', async () => {
    mockApiService.getHello.mockReturnValue(of({ message: 'Hello from Django!', ping_count: 5 }));
    const { fixture, el } = await render();
    fixture.componentInstance.ping();
    await fixture.whenStable();
    expect(el.querySelector('.message')?.textContent?.trim()).toBe('Hello from Django!');
    expect(el.querySelector('.count')?.textContent?.trim()).toBe('Ping count: 5');
  });

  it('should display error when backend is unreachable', async () => {
    mockApiService.getHello.mockReturnValue(throwError(() => new Error('Network error')));
    const { fixture, el } = await render();
    fixture.componentInstance.ping();
    await fixture.whenStable();
    expect(el.querySelector('.error')?.textContent?.trim()).toBe(
      'Could not connect to Django backend.',
    );
  });

  it('should call getHello when ping button is clicked', async () => {
    mockApiService.getHello.mockReturnValue(NEVER);
    const { el } = await render();
    el.querySelector('button')?.click();
    expect(mockApiService.getHello).toHaveBeenCalledTimes(1);
  });
});
