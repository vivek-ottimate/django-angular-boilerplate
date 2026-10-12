import { Component, inject, signal } from '@angular/core';
import { ApiService } from './api.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly api = inject(ApiService);

  protected readonly message = signal('');
  protected readonly pingCount = signal<number | null>(null);
  protected readonly error = signal('');
  protected readonly loading = signal(false);

  ping() {
    this.loading.set(true);
    this.error.set('');
    this.api.getHello().subscribe({
      next: (data) => {
        this.message.set(data.message);
        this.pingCount.set(data.ping_count);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Could not connect to Django backend.');
        this.loading.set(false);
      },
    });
  }
}
