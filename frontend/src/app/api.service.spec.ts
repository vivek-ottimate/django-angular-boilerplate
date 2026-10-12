import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ApiService } from './api.service';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should GET /api/hello/ and return message', () => {
    let result: unknown;
    service.getHello().subscribe((data) => (result = data));

    const req = httpMock.expectOne('/api/hello/');
    expect(req.request.method).toBe('GET');
    req.flush({ message: 'Hello from Django!', ping_count: 1 });

    expect(result).toEqual({ message: 'Hello from Django!', ping_count: 1 });
  });
});
