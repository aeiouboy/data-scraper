describe('Simple Test', () => {
  it('should pass basic test', () => {
    expect(1 + 1).toBe(2);
  });

  it('should test basic string matching', () => {
    expect('hello world').toContain('world');
  });
});